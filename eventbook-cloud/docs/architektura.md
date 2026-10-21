# EventBook Cloud – architektúra (tervezet)

## Komponensek
- Frontend: Nginx statikus HTML/CSS/JavaScript kiszolgáló, Bootstrap 5 felülettel.
- Backend: Python Flask REST API.
- Adatbázis: PostgreSQL; helyben Docker Compose, AWS-ben Amazon RDS.
- Objektumtároló: Amazon S3 a rendezvényplakátokhoz.
- Serverless komponens: AWS Lambda QR-kód vagy jegyartefaktum generálásához.
- Compute: külön frontend és backend konténer/szolgáltatás.
- Hálózat: AWS VPC, elkülönített hálózati rétegek és security groupok.

## Foglalási folyamat
1. A bejelentkezett felhasználó kiválasztja a jegytípust és darabszámot.
2. A backend ellenőrzi a bemeneti adatokat és zárolja a jegytípus rekordját.
3. A backend ellenőrzi a készletet, létrehozza a foglalást, majd növeli a lefoglalt mennyiséget.
4. A tranzakció commit után a felhasználó foglalási azonosítót kap.
5. A QR-kód a foglalási kódot reprezentálja; önmagában nem beléptetési validáció.

## Fontos tervezési megjegyzés
A jelenlegi helyi MVP QR-kódja az API-n készül. Az AWS Lambda-integráció a felhős szakaszban kerül bevezetésre. A ténylegesen telepített architektúra végleges ábráját a valós AWS-erőforrások alapján kell frissíteni.

## Orchestration
Docker Compose a helyi fejlesztői környezetet koordinálja, de nem feltétlenül számít klaszter-orchestrátornak az oktatói értékelésben. A követelményt oktatóval kell tisztázni; szükség esetén ECS vagy más elfogadott megoldás kerül be.
