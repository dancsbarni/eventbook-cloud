# EventBook Cloud

Cooltix-jellegű rendezvény- és jegyfoglaló rendszer egyetemi AWS-projekthez.

## Funkciók
- Rendezvények listázása és részletes megtekintése
- Regisztráció, bejelentkezés, kijelentkezés
- Admin szerepkör és rendezvény CRUD
- Jegytípusok, kapacitásellenőrzés és foglalás tranzakcióban
- Saját foglalások és QR-kódos digitális jegy
- Docker Compose fejlesztői környezet
- PostgreSQL adatbázis
- AWS S3 / Lambda integráció előkészítve

> Ez az első fejlesztési csomag: a helyi MVP alapja. Az AWS-infrastruktúrát, S3/Lambda éles integrációt, teljes tesztcsomagot és végleges dokumentációt külön lépésekben készítjük el és ellenőrizzük.

## Indítás Windows alatt
Előfeltétel: Docker Desktop fut.

1. Másold a `.env.example` fájlt `.env` néven.
2. A `SECRET_KEY` értékét cseréld le egy saját, véletlenszerű titokra.
3. PowerShellben a projekt gyökérmappájában:
   ```powershell
   docker compose up --build
   ```
4. Nyisd meg: http://localhost:8080

A backend közvetlenül is elérhető a `http://localhost:5000/health` címen.

## Első admin felhasználó
Az első regisztrált felhasználó normál felhasználó. Az admin szerepkört ne nyilvános regisztrációs mezőből lehessen kiválasztani. Fejlesztéshez az admin szerepkör a `scripts/promote_admin.py` szkripttel állítható be a konténeren belül.

```powershell
docker compose exec backend python scripts/promote_admin.py user@example.com
```

## Mappastruktúra
- `backend/`: Flask REST API, adatbázismodellek és üzleti logika
- `frontend/`: statikus Bootstrap felület
- `database/`: SQL séma és fejlesztői seed adatok
- `infra/`: későbbi AWS infrastruktúra leírások
- `docs/`: dokumentáció vázlata és tesztterv

## Biztonsági megjegyzések
- Ne tölts fel `.env` fájlt vagy AWS-kulcsokat GitHubra.
- Éles környezetben kötelező HTTPS, erős `SECRET_KEY`, korlátozott IAM-szerepkörök és privát adatbázis.
- Ez oktatási MVP, nem éles fizetési rendszer.
