# AWS költségellenőrzési lista

Saját AWS-fiókban minden létrehozás előtt ellenőrizd a régiót, a várható díjakat és a jogosultságokat.

- Állíts be AWS Budgets költségkeretet és e-mail-riasztást.
- RDS, ALB, NAT Gateway és nyilvános IPv4-cím díjköteles lehet akkor is, ha a forgalom kicsi.
- Ne hozz létre NAT Gatewayt, ALB-t vagy RDS-t addig, amíg nem tisztáztuk a beadandó követelményeit és költségét.
- Ne tegyél adatbázis-jelszót, AWS access key-t vagy Flask SECRET_KEY-t GitHubra.
- Használj IAM szerepkört az EC2 és Lambda számára; kerüld a hosszú élettartamú access key-ket.
- A beadás után ellenőrizd az EC2, RDS, EBS, Load Balancer, NAT Gateway, Elastic IP és egyéb erőforrásokat.
- A költségkeret-riasztás nem feltétlenül állítja le automatikusan a szolgáltatásokat.
