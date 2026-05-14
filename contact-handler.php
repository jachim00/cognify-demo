<?php
/**
 * contact-handler.php
 *
 * Handler formularza kontaktowego dla cognify.pl.
 * Wysyla mail przez smtp.home.pl jako kontakt@cognify.pl, do kontakt@cognify.pl,
 * z Reply-To nadawcy. Honeypot anti-spam.
 *
 * Wymagania na hostingu:
 *   /contact-handler.php       <- ten plik (w roocie)
 *   /_secrets/.env             <- konfiguracja SMTP (poza HTTP)
 *   /_secrets/.htaccess        <- blokada HTTP do _secrets/
 *   /dziekujemy/index.html     <- strona po sukcesie (juz istnieje)
 */

declare(strict_types=1);

// ---------------------------------------------------------------------------
// CONFIG
// ---------------------------------------------------------------------------
const REQUIRED_FIELDS = ['Name', 'Email', 'Message'];
const MAX_MESSAGE_LEN = 5000;
const SUCCESS_REDIRECT = '/dziekujemy/';
const ERROR_REDIRECT_BASE = '/?contact=error&reason=';

// ---------------------------------------------------------------------------
// LOAD .env
// ---------------------------------------------------------------------------
function load_env(): array {
    $candidates = [
        __DIR__ . '/_secrets/.env',
        dirname(__DIR__) . '/_secrets/.env',
    ];
    foreach ($candidates as $p) {
        if (!is_readable($p)) continue;
        $env = [];
        foreach (file($p, FILE_IGNORE_NEW_LINES | FILE_SKIP_EMPTY_LINES) as $line) {
            $line = trim($line);
            if ($line === '' || $line[0] === '#') continue;
            $eq = strpos($line, '=');
            if ($eq === false) continue;
            $k = trim(substr($line, 0, $eq));
            $v = trim(substr($line, $eq + 1));
            if (strlen($v) >= 2 && (($v[0] === '"' && substr($v, -1) === '"') || ($v[0] === "'" && substr($v, -1) === "'"))) {
                $v = substr($v, 1, -1);
            }
            $env[$k] = $v;
        }
        return $env;
    }
    return [];
}

function redirect(string $url): void {
    header("Location: $url", true, 302);
    exit;
}

function fail(string $reason, int $http = 302): void {
    if ($http === 302) {
        redirect(ERROR_REDIRECT_BASE . urlencode($reason));
    }
    http_response_code($http);
    header('Content-Type: text/plain; charset=utf-8');
    echo "Blad: $reason";
    exit;
}

// ---------------------------------------------------------------------------
// SMTP — pure-PHP klient (socket + AUTH LOGIN + SSL/TLS)
// ---------------------------------------------------------------------------
class SmtpClient {
    private $sock;
    private bool $debug;
    private array $log = [];

    public function __construct(bool $debug = false) {
        $this->debug = $debug;
    }

    public function connect(string $host, int $port, string $secure, int $timeout = 30): void {
        $remote = ($secure === 'ssl') ? "ssl://$host:$port" : "tcp://$host:$port";
        $ctx = stream_context_create([
            'ssl' => [
                'verify_peer' => true,
                'verify_peer_name' => true,
                'allow_self_signed' => false,
                'SNI_enabled' => true,
            ],
        ]);
        $errno = 0; $errstr = '';
        $this->sock = @stream_socket_client($remote, $errno, $errstr, $timeout, STREAM_CLIENT_CONNECT, $ctx);
        if (!$this->sock) {
            throw new RuntimeException("SMTP connect failed: $errstr ($errno)");
        }
        stream_set_timeout($this->sock, $timeout);
        $this->expect(220);

        $this->send("EHLO cognify.pl");
        $this->expect(250);

        if ($secure === 'tls') {
            $this->send("STARTTLS");
            $this->expect(220);
            if (!stream_socket_enable_crypto($this->sock, true, STREAM_CRYPTO_METHOD_TLS_CLIENT)) {
                throw new RuntimeException('STARTTLS handshake failed');
            }
            $this->send("EHLO cognify.pl");
            $this->expect(250);
        }
    }

    public function auth(string $user, string $pass): void {
        $this->send("AUTH LOGIN");
        $this->expect(334);
        $this->send(base64_encode($user));
        $this->expect(334);
        $this->send(base64_encode($pass));
        $code = $this->expect([235, 535]);
        if ($code === 535) {
            throw new RuntimeException('SMTP auth failed (535)');
        }
    }

    public function sendMail(string $from, array $to, string $rawMessage): void {
        $this->send("MAIL FROM:<$from>");
        $this->expect(250);
        foreach ($to as $r) {
            $this->send("RCPT TO:<$r>");
            $this->expect([250, 251]);
        }
        $this->send("DATA");
        $this->expect(354);
        // CRLF and dot-stuffing
        $rawMessage = preg_replace("/(?<!\r)\n/", "\r\n", $rawMessage);
        $rawMessage = preg_replace("/^\\./m", "..", $rawMessage);
        fwrite($this->sock, $rawMessage . "\r\n.\r\n");
        $this->expect(250);
    }

    public function quit(): void {
        if ($this->sock) {
            @$this->send("QUIT");
            @fclose($this->sock);
        }
    }

    private function send(string $cmd): void {
        if ($this->debug) $this->log[] = "> $cmd";
        fwrite($this->sock, "$cmd\r\n");
    }

    private function expect($wanted): int {
        $code = 0;
        $line = '';
        do {
            $line = fgets($this->sock, 1024);
            if ($line === false) throw new RuntimeException('SMTP read failed');
            if ($this->debug) $this->log[] = "< " . rtrim($line);
            $code = (int) substr($line, 0, 3);
            $sep  = $line[3] ?? ' ';
        } while ($sep === '-');
        $wantedArr = is_array($wanted) ? $wanted : [$wanted];
        if (!in_array($code, $wantedArr, true)) {
            throw new RuntimeException("SMTP unexpected $code (wanted " . implode('/', $wantedArr) . "): " . trim($line));
        }
        return $code;
    }

    public function getLog(): array { return $this->log; }
}

// ---------------------------------------------------------------------------
// MAIN
// ---------------------------------------------------------------------------

if ($_SERVER['REQUEST_METHOD'] !== 'POST') {
    fail('method', 405);
}

$env = load_env();
foreach (['SMTP_HOST','SMTP_PORT','SMTP_SECURE','SMTP_USER','SMTP_PASS','SMTP_FROM','MAIL_TO'] as $k) {
    if (empty($env[$k])) fail("config:$k", 500);
}

// --- Honeypot: jesli pole _honey wypelnione, udaj sukces (nie pokazuj botowi ze odrzucono) ---
if (!empty($_POST['_honey'])) {
    redirect(SUCCESS_REDIRECT);
}

// --- Walidacja pol ---
$data = [];
foreach (REQUIRED_FIELDS as $f) {
    $v = trim((string)($_POST[$f] ?? ''));
    if ($v === '') fail('missing:' . strtolower($f));
    $data[$f] = $v;
}

if (!filter_var($data['Email'], FILTER_VALIDATE_EMAIL)) {
    fail('invalid_email');
}
if (mb_strlen($data['Message']) > MAX_MESSAGE_LEN) {
    fail('message_too_long');
}

// --- Dodatkowe pola opcjonalne (kazdy poza REQUIRED i polach servicowych wlasnych) ---
$skipFields = array_merge(REQUIRED_FIELDS, ['_honey', '_subject', '_next', '_redirect', '_captcha', '_template']);
$extra = [];
foreach ($_POST as $k => $v) {
    if (in_array($k, $skipFields, true)) continue;
    if (is_array($v)) $v = implode(', ', $v);
    $v = trim((string)$v);
    if ($v !== '') $extra[$k] = $v;
}

// --- Body maila ---
$subject = !empty($_POST['_subject']) ? trim((string)$_POST['_subject']) : 'Nowe zapytanie z cognify.pl';
$subject = mb_substr(preg_replace('/[\r\n]+/', ' ', $subject), 0, 200);

$body  = "Nowa wiadomosc z formularza kontaktowego cognify.pl\n";
$body .= str_repeat('=', 60) . "\n\n";
$body .= "Imie / Firma:  " . $data['Name'] . "\n";
$body .= "Email:         " . $data['Email'] . "\n";
foreach ($extra as $k => $v) {
    $body .= str_pad("$k:", 14, ' ', STR_PAD_RIGHT) . $v . "\n";
}
$body .= "\nWiadomosc:\n";
$body .= "----------\n";
$body .= $data['Message'] . "\n\n";
$body .= str_repeat('-', 60) . "\n";
$body .= "Wyslane:       " . date('Y-m-d H:i:s') . "\n";
$body .= "IP:            " . ($_SERVER['REMOTE_ADDR'] ?? '?') . "\n";
$body .= "User-Agent:    " . substr((string)($_SERVER['HTTP_USER_AGENT'] ?? '?'), 0, 200) . "\n";
$body .= "Referer:       " . substr((string)($_SERVER['HTTP_REFERER'] ?? '?'), 0, 200) . "\n";

// --- Naglowki RFC 5322 ---
$fromAddr = $env['SMTP_FROM'];
$fromName = $env['SMTP_FROM_NAME'] ?? 'Cognify';
$toAddr   = $env['MAIL_TO'];

$boundary = 'cognify-' . bin2hex(random_bytes(8));
$messageId = '<' . bin2hex(random_bytes(8)) . '@cognify.pl>';

// Naglowek From — encoded
$fromHeader = '=?UTF-8?B?' . base64_encode($fromName) . "?= <$fromAddr>";

$replyToName = $data['Name'];
$replyToHeader = '=?UTF-8?B?' . base64_encode($replyToName) . '?= <' . $data['Email'] . '>';

$subjectHeader = '=?UTF-8?B?' . base64_encode($subject) . '?=';

$headers  = "From: $fromHeader\r\n";
$headers .= "To: $toAddr\r\n";
$headers .= "Reply-To: $replyToHeader\r\n";
$headers .= "Subject: $subjectHeader\r\n";
$headers .= "Date: " . date('r') . "\r\n";
$headers .= "Message-ID: $messageId\r\n";
$headers .= "MIME-Version: 1.0\r\n";
$headers .= "Content-Type: text/plain; charset=UTF-8\r\n";
$headers .= "Content-Transfer-Encoding: 8bit\r\n";
$headers .= "X-Mailer: cognify-form/1.0\r\n";
$headers .= "X-Originating-IP: " . ($_SERVER['REMOTE_ADDR'] ?? '') . "\r\n";

$rawMessage = $headers . "\r\n" . $body;

// --- Wysylka ---
// Probujemy SMTP, jesli wszystkie hosty padna -> fallback mail() PHP.
$smtpHosts = [
    [$env['SMTP_HOST'], (int)$env['SMTP_PORT'], $env['SMTP_SECURE']],
    ['localhost',   25,  'none'],
    ['127.0.0.1',   25,  'none'],
    ['localhost',   587, 'tls'],
];

$lastError = '';
$sentViaSmtp = false;
foreach ($smtpHosts as [$host, $port, $secure]) {
    $smtp = new SmtpClient(false);
    try {
        $smtp->connect($host, $port, $secure);
        if ($secure !== 'none') {
            $smtp->auth($env['SMTP_USER'], $env['SMTP_PASS']);
        }
        $smtp->sendMail($fromAddr, [$toAddr], $rawMessage);
        $smtp->quit();
        $sentViaSmtp = true;
        break;
    } catch (Throwable $e) {
        $lastError = "$host:$port($secure) " . $e->getMessage();
        error_log("contact-handler SMTP try $host:$port - " . $e->getMessage());
        try { $smtp->quit(); } catch (Throwable $_) {}
    }
}

if (!$sentViaSmtp) {
    // Fallback: natywny mail() PHP
    $mailHeaders =
        "From: $fromHeader\r\n" .
        "Reply-To: $replyToHeader\r\n" .
        "Date: " . date('r') . "\r\n" .
        "Message-ID: $messageId\r\n" .
        "MIME-Version: 1.0\r\n" .
        "Content-Type: text/plain; charset=UTF-8\r\n" .
        "Content-Transfer-Encoding: 8bit\r\n" .
        "X-Mailer: cognify-form/1.0-mail\r\n";
    $sentOk = @mail($toAddr, $subjectHeader, $body, $mailHeaders, "-f $fromAddr");
    if (!$sentOk) {
        error_log("contact-handler: SMTP failed AND mail() failed. Last SMTP error: $lastError");
        fail('smtp:' . substr($lastError, 0, 80));
    }
}

// --- Sukces ---
$next = !empty($_POST['_next']) ? (string)$_POST['_next'] : SUCCESS_REDIRECT;
// Walidacja redirect — tylko lokalne sciezki
if (!preg_match('#^/[a-zA-Z0-9_/.-]*$#', $next) && !preg_match('#^https?://cognify\.pl/#i', $next)) {
    $next = SUCCESS_REDIRECT;
}
redirect($next);
