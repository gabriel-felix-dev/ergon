"""Local SMTP sink for manual integration tests; no email leaves this machine."""

import json
import socketserver
from datetime import datetime, timezone
from pathlib import Path


OUTPUT = Path(__file__).resolve().parents[1] / ".test-mail" / "messages.jsonl"


class SMTPHandler(socketserver.StreamRequestHandler):
    def send(self, response):
        self.wfile.write((response + "\r\n").encode("ascii"))
        self.wfile.flush()

    def handle(self):
        self.send("220 localhost Ergon test mail")
        sender = None
        recipients = []
        while line := self.rfile.readline():
            command = line.decode("utf-8", "replace").strip()
            upper = command.upper()
            if upper.startswith("EHLO"):
                self.send("250-localhost")
                self.send("250 SIZE 10485760")
            elif upper.startswith("HELO"):
                self.send("250 localhost")
            elif upper.startswith("MAIL FROM:"):
                sender = command[10:]
                self.send("250 OK")
            elif upper.startswith("RCPT TO:"):
                recipients.append(command[8:])
                self.send("250 OK")
            elif upper == "DATA":
                self.send("354 End data with <CR><LF>.<CR><LF>")
                lines = []
                while data_line := self.rfile.readline():
                    if data_line in (b".\r\n", b".\n"):
                        break
                    if data_line.startswith(b".."):
                        data_line = data_line[1:]
                    lines.append(data_line)
                OUTPUT.parent.mkdir(exist_ok=True)
                with OUTPUT.open("a", encoding="utf-8") as output:
                    output.write(json.dumps({
                        "at": datetime.now(timezone.utc).isoformat(),
                        "sender": sender,
                        "recipients": recipients,
                        "data": b"".join(lines).decode("utf-8", "replace"),
                    }, ensure_ascii=False) + "\n")
                self.send("250 OK")
            elif upper == "RSET":
                sender = None
                recipients = []
                self.send("250 OK")
            elif upper == "NOOP":
                self.send("250 OK")
            elif upper == "QUIT":
                self.send("221 Bye")
                break
            else:
                self.send("502 Command not implemented")


class Server(socketserver.ThreadingTCPServer):
    allow_reuse_address = True
    daemon_threads = True


if __name__ == "__main__":
    with Server(("127.0.0.1", 1025), SMTPHandler) as server:
        print("Capturing test mail at 127.0.0.1:1025", flush=True)
        server.serve_forever()
