"""T014 (MANUÁLIS KAPU): Kimi Code bejelentkezés az lm15-be.

Futtatás interaktív terminálban (a felhasználó végzi, agent nem):

    .venv\\Scripts\\python.exe scripts\\login_kimi.py            # alap host (auth.kimi.com)
    .venv\\Scripts\\python.exe scripts\\login_kimi.py --kimi-ai  # nemzetközi host (auth.kimi.ai)

A folyamat eszközkódot ad; a sikeres bejelentkezés mentődik.
"""
import sys

from lm15.login import Auth, TerminalUI

settings = {}
if "--kimi-ai" in sys.argv:
    settings["oauth_host"] = "https://auth.kimi.ai"
    print("host: auth.kimi.ai (nemzetközi)")
else:
    print("host: auth.kimi.com (alapértelmezett)")

auth = Auth.local()
print("meglévő kapcsolatok:", auth.connections())
conn = auth.login("kimi-code", ui=TerminalUI(), settings=settings or None,
                  allow_unverified=True)
print("bejelentkezve:", conn)
print("kapcsolatok:", auth.connections())
