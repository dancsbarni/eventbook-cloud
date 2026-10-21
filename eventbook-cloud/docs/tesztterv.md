# Tesztterv – EventBook Cloud

## Funkcionális tesztek
1. A kezdőoldal betölti a közzétett rendezvényeket.
2. A keresés cím és helyszín alapján szűr.
3. A regisztráció elutasítja a hiányos vagy érvénytelen adatokat.
4. Azonos e-mail-címmel nem lehet második fiókot létrehozni.
5. Hibás jelszóval a belépés sikertelen.
6. Vendég nem tud foglalást készíteni.
7. A felhasználó csak a saját foglalásait látja.
8. A felhasználó nem fér hozzá admin API-hoz.
9. Az admin létrehozhat rendezvényt.
10. Az admin archiválhat rendezvényt.
11. A foglalás nem lépheti túl a jegytípus szabad kapacitását.
12. A sikeres foglaláshoz egyedi foglalási kód készül.
13. A jogosult felhasználó le tudja kérni a saját QR-kódját.
14. Az admin látja a foglalási statisztikákat.
15. A plakátfeltöltés konfigurált S3-bucket mellett működik.

## Nem funkcionális ellenőrzések
- Mobilon is használható felület.
- Jelszavak hash-elve tárolódnak.
- Titkok nem szerepelnek a Git-repozitóriumban.
- Adatbázis csak a szükséges hálózati forrásból elérhető.
- A `GET /health` végpont elérhető.
- Docker Compose újraindítás után az adatok megmaradnak a volume-ban.

## Eredményrögzítés
A beadandó végleges verziójában minden teszthez rögzíteni kell a tényleges eredményt, dátumot és szükség esetén képernyőképet. Nem szabad nem futtatott tesztet sikeresként feltüntetni.
