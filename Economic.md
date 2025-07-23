

---
# 🌐 **TokenizeLocal**  
## **Tokenisation des petites entreprises avec versement automatique de dividendes**
---
## 🔍 1. Problème  
Les petites et moyennes entreprises font face à plusieurs problèmes :  
| Problème | Description |  
|--------|----------|  
| Manque d'investissements | Les banques prêtent difficilement, et les fonds ignorent souvent les petits projets. |  
| Liquidité de la part dans l'entreprise | Il est difficile pour les investisseurs de sortir de l'investissement ou de revendre leur part. |  
| Confiance dans les données | Les rapports financiers sont souvent indisponibles ou opaques. |  
| Distribution des bénéfices | Absence de mécanisme de répartition automatique des revenus entre les investisseurs. |  
---
## 💡 2. Solution  
**TokenizeLocal** est une plateforme de tokenisation des parts d’entreprise via un système centralisé basé sur une base de données. Elle permet :  
- À l’entreprise d’émettre des jetons liés à une part de son chiffre d’affaires.  
- Aux investisseurs d’acheter des jetons et de recevoir des **dividendes mensuels**.  
- À la plateforme d’évoluer d’une simple base de données vers un écosystème blockchain.
---
## 📈 3. Fonctionnement
### Pour l’entreprise :
1. **Inscription via l’INN** → Le statut de l’entreprise est vérifié via l’API Checko.  
2. **Émission de jetons** → Détermination du nombre de jetons et du pourcentage du chiffre d’affaires à distribuer.  
3. **Mise à jour des données de revenus** → Transmission des données de chiffre d’affaires au système.  
4. **Distribution automatique des dividendes** → Répartition de la somme entre tous les détenteurs de jetons.  
### Pour l’utilisateur / investisseur :
1. **Inscription / authentification** → Email + mot de passe.  
2. **Choix de l’entreprise** → Consultation des entreprises et des jetons disponibles.  
3. **Achat de jetons** → L’utilisateur reçoit les jetons.  
4. **Dividendes mensuels** → Paiements proportionnels au nombre de jetons détenus.  
---
## 🧩 4. Structure du projet  
Le système repose initialement sur une base de données centralisée (`SQLite`), avec possibilité d’évolution future :  
- **blockchain/db_manager.py** — Gestion des entreprises, jetons et soldes utilisateurs.  
- **verification/api_client.py** — Vérification du statut de l’entreprise via l’API Checko.  
- **utils/logger.py** — Journalisation des événements.  
- **main.py** — Point d’entrée, implémentation de toute la logique métier.  
- **blockchain/users.py** — Inscription et authentification des utilisateurs.  
- **blockchain/register_user.py** — Script d’inscription autonome.  
- **blockchain/records_check.py** — Vérification du contenu de la base de données.  
---
## 📁 5. Tables de la base de données  
| Table | Description |  
|--------|----------|  
| `businesses` | Stocke l’INN et le nom de l’entreprise |  
| `token_issuances` | Nombre de jetons émis |  
| `users` | Email, nom, mot de passe |  
| `user_tokens` | Solde de jetons de chaque utilisateur |  
| `dividend_history` *(optionnel)* | Historique des paiements de dividendes |  
---
## 💰 6. Mécanisme de versement des dividendes  
Chaque mois, le système :  
1. Récupère le chiffre d’affaires de l’entreprise (par exemple, depuis les rapports financiers).  
2. Fixe le montant des dividendes (par exemple, 10 % du chiffre d’affaires).  
3. Répartit l’argent proportionnellement au nombre de jetons détenus par chaque utilisateur.  
### Exemple :  
- Nombre total de jetons : **10 000**  
- Bénéfice de l’entreprise : **10 000 $**  
- Pourcentage de dividendes : **10 %**  
- Fonds total de dividendes : **1 000 $**  
👉 Un utilisateur possédant 200 jetons reçoit :  
**1 000 $ × (200 / 10 000) = 20 $**
---
## 📊 7. Modèle économique  
### Prix du jeton  
Déterminé par le chiffre d’affaires de l’entreprise et le nombre de jetons émis.  
Exemple :  
- L’entreprise génère 10 000 $ de chiffre d’affaires par mois.  
- Alloue 10 % → 1 000 $ aux jetons.  
- Émet 10 000 jetons → **1 jeton = 0,10 $ par mois**.  
### ROI (Retour sur investissement)  
Si un investisseur achète 1 000 jetons pour 100 $ → il reçoit 10 $/mois → **ROI ~10 % par mois**.  
---
## 🔄 8. Marché secondaire des jetons  
Actuellement, les jetons sont enregistrés dans la base de données, mais la revente est déjà prévue.  
À l’avenir, une DEX interne peut être lancée, où :  
- Le prix du jeton est fixé par l’offre et la demande.  
- Les jetons peuvent être échangés entre utilisateurs.  
- Le prix dépend de la croissance de l’entreprise et de son chiffre d’affaires.  
---
## 📉 9. Facteurs influençant le prix du jeton ?  
| Facteur | Impact |  
|--------|----------|  
| Croissance du chiffre d’affaires | ➕ Les jetons augmentent en valeur |  
| Prolongation de la période de dividendes | ➕ Valeur totale accrue |  
| Augmentation du pourcentage du chiffre d’affaires | ➕ Dividendes plus élevés |  
| Baisse du chiffre d’affaires | ➖ Les jetons perdent de la valeur |  
| Liquidation de l’entreprise | ❌ Les jetons deviennent sans valeur |  
---
## 📦 10. Possibilités d’évolutivité  
| Possibilité | Description |  
|------------|----------|  
| **Gouvernance DAO** | Les investisseurs peuvent voter sur le développement de l’entreprise |  
| **Marché secondaire** | Revente de jetons entre utilisateurs |  
| **Intégration blockchain** | Support de Polygon / TON pour un marché décentralisé |  
| **Investisseurs internationaux** | Support de USDT, USDC, ETH |  
| **Assurance des actifs** | Protection contre la faillite via un DAO |  
| **Paiements en stablecoins** | Pour minimiser la volatilité |  
---
## 📈 11. Avantages pour les parties prenantes  
### 👤 Pour l’utilisateur / investisseur :  
- Reçoit des dividendes réguliers.  
- Peut acheter un seul jeton.  
- Si l’entreprise progresse, la valeur du jeton augmente.  
- Peut revendre les jetons avec profit.  
- Toutes les données sont transparentes.  
### 🏢 Pour l’entreprise :  
- Obtient du capital sans intérêts bancaires.  
- Peut attirer des investisseurs internationaux.  
- Modèle d’émission flexible.  
- Paiements automatiques.  
- Possibilité de croissance grâce au vote des investisseurs.  
---
## 📊 12. Exemple de modèle : Café "Chokoladnitsa"  
### Hypothèses :  
- Émission : 10 000 jetons.  
- Part des dividendes : 10 % du chiffre d’affaires.  
- Chiffre d’affaires moyen : 10 000 $/mois.  
- ROI : 10 000 $ × 10 % = 1 000 $/mois  
👉 Un utilisateur possédant 1 000 jetons reçoit 100 $ par an au départ.  
Si l’entreprise double de taille, les dividendes doublent également.  
---
## 📈 13. Prévision d’évolution de la valeur du jeton  
| Mois | Chiffre d’affaires | Pools de dividendes | Prix du jeton |  
|-------|--------|------------------|-------------|  
| 1     | 10 000 $ | 1 000 $           | 0,10 $       |  
| 3     | 12 000 $ | 1 200 $           | 0,12 $       |  
| 6     | 15 000 $ | 1 500 $           | 0,15 $       |  
| 9     | 18 000 $ | 1 800 $           | 0,18 $       |  
| 12    | 20 000 $ | 2 000 $           | 0,20 $       |  
👉 Le prix du jeton a augmenté de **100 % sur un an**.  
👉 Les dividendes ont rapporté 1 200 $.  
👉 ROI total : **220 % sur un an**.  
---
## 📈 14. Que se passe-t-il lorsque le chiffre d’affaires de l’entreprise augmente ?
### 1. **Comment la croissance du chiffre d’affaires affecte-t-elle le jeton ?**  
Quand l’entreprise augmente son chiffre d’affaires, la somme disponible pour la distribution de dividendes augmente automatiquement.  
#### Formule :  
$$
\text{Dividende par jeton} = \frac{\text{Chiffre d'affaires de l'entreprise} \times \text{Part des dividendes}}{\text{Nombre total de jetons}}
$$
**Exemple :**  
- Jetons émis : 10 000  
- Part des dividendes : 10 %  
- Chiffre d’affaires mensuel : 10 000 $ → puis croît jusqu’à 20 000 $  
| Mois | Chiffre d’affaires | Pools de dividendes | Prix du jeton |  
|-------|--------|------------------|-------------|  
| 1     | 10 000 $ | 1 000 $           | 0,10 $       |  
| 12    | 20 000 $ | 2 000 $           | 0,20 $       |  
👉 Autrement dit, **le prix du jeton double**, si la part des dividendes reste identique et que le nombre de jetons ne change pas.  
---
## 💡 Quels sont les avantages pour l’investisseur ?  
### A. **Dividendes mensuels**  
L’investisseur reçoit un **revenu passif stable**. Par exemple, avec 1 000 jetons :  
- Mois 1 : 0,10 $ × 1 000 = 10 $  
- Mois 12 : 0,20 $ × 1 000 = 20 $  
👉 Autrement dit, **le revenu augmente proportionnellement à la croissance de l’entreprise**.  
### B. **Croissance de la valeur du jeton**  
Si l’entreprise croît et que le jeton prend de la valeur, l’investisseur peut :  
- **Revendre les jetons avec profit** sur le marché secondaire.  
- **Conserver les jetons** et recevoir encore plus de dividendes.  
👉 L’investisseur obtient donc **un double avantage** : hausse du prix et hausse des dividendes.  
---
## ⚠️ Où se situent les points faibles ?  
### 1. **Le prix du jeton dépend du chiffre d’affaires, pas de la demande du marché**  
- Actuellement, le prix du jeton est calculé **algorithmiquement**, basé sur le chiffre d’affaires.  
- Cela **ne tient pas compte des facteurs du marché** (par exemple, la demande pour le jeton, les attentes des investisseurs, la conjoncture macroéconomique).  
- Cela peut entraîner un **déséquilibre**, si le chiffre d’affaires baisse mais que le jeton vaut déjà plus que sa "valeur réelle".  
### 2. **Absence de marché réel au départ**  
- Tant que les jetons sont stockés dans la base de données, **ils ne peuvent pas être librement échangés**.  
- L’investisseur ne peut sortir que via :  
  - **Rachat des jetons par l’entreprise**  
  - **Attente de la croissance des dividendes**  
- Cela réduit la **liquidité**.  
### 3. **Dépendance à la précision des données de chiffre d’affaires**  
- Si l’entreprise fournit des **données incorrectes**, cela affecte le calcul des dividendes.  
- Il faut intégrer une **vérification via Open Banking ou les systèmes comptables**.  
### 4. **Dépendance à une seule entreprise**  
- Si un investisseur a acheté les jetons d’un seul café, et qu’il ferme → **tout l’investissement est perdu**.  
- Il faut proposer :  
  - **Diversification** (investir dans plusieurs entreprises)  
  - **Assurance des jetons**  
---
## 🧠 Comment améliorer cela ?  
### 1. **Ajouter un marché secondaire**  
- Permettre aux investisseurs de **revendre les jetons entre eux**.  
- Fixer le prix du jeton via **l’offre et la demande**, et non seulement via le chiffre d’affaires.  
- Cela augmentera la **liquidité** et permettra aux investisseurs de **sortir de l’investissement**.  
### 2. **Intégration avec la blockchain**  
- Passer à un **système décentralisé**.  
- Stocker les jetons dans des portefeuilles, utiliser des **contrats intelligents** pour le paiement des dividendes.  
- Cela augmentera la **confiance et la transparence**.  
### 3. **Introduire une assurance**  
- Créer un **fonds d’assurance** (par exemple via un DAO), où l’entreprise paie une petite commission.  
- Si l’entreprise ferme → les investisseurs reçoivent une compensation partielle.  
### 4. **Rachat automatique de jetons**  
- L’entreprise peut **racheter des jetons au prix actuel**, afin de :  
  - Réduire la part des investisseurs  
  - Augmenter la liquidité  
---
## 📦 15. Marché secondaire des jetons  
Au départ, les jetons sont stockés dans la base de données, mais la possibilité de revente est déjà prévue.  
### Avantages du marché secondaire :  
- L’investisseur peut **revendre des jetons** à un autre utilisateur.  
- Le prix est fixé par **l’offre et la demande**.  
- Si l’entreprise croît, le prix du jeton augmente aussi.  
- Les utilisateurs peuvent sortir de l’investissement avant la fin de la période.  
---
## 📊 16. Monétisation de la plateforme  
| Étape | À mettre en œuvre | Commission |  
|------|----------------|-----------|  
| Émission de jetons | L’entreprise paie pour la tokenisation | 3–5 % du montant levé |  
| Achat de jetons | La plateforme prélève une commission | 0,5–1 % |  
| Transfert de jetons | Revente de jetons | 0,1–0,5 % |  
| Listing premium | Offres en vedette | 500–1 000 $ par mise en avant |  
| Analytique | Rapports sur l’entreprise | 10–50 $ par mois |  
| Programme d’affiliation | Recrutement de nouveaux participants | 2–5 % par parrainage |  
---
## 📈 17. Prévision de croissance  
| Période | Entreprises | Investisseurs | Revenus |  
|--------|----------|-----------|--------|  
| Année 1 | 100      | 10 000    | 1 M$+ |  
| Année 2 | 1 000    | 100 000   | 10 M$+ |  
| Année 3 | 10 000   | 1 M+      | 100 M$+ |  
---
## 🧠 18. Avantages concurrentiels  
| Avantage | Mise en œuvre |  
|-------------|------------|  
| Transparence | Toutes les données sont visibles dans la base de données |  
| Dividendes automatiques | Paiements mensuels |  
| Modèle centralisé | Lancement rapide, coûts faibles |  
| Conformité réglementaire | Émission via SPV dans des juridictions régulées |  
| Flexibilité du modèle | Adaptation facile à tout créneau |  
| Accès mondial | Support de USDT, USDC, ETH |  
---
## 🌍 19. Public cible  
| Catégorie | Description |  
|-----------|----------|  
| Petites entreprises | Cafés, boutiques, distributeurs automatiques, stations solaires |  
| Investisseurs individuels | Personnes souhaitant investir dans l’économie réelle |  
| Plateformes de crowdfunding | Intégration avec des systèmes existants |  
| Communautés DAO | Gestion collective d’actifs |  
| Fonds RWA | Fonds souhaitant se diversifier |  
---
## 🚀 20. Possibilités d’évolutivité  
| Étape | À faire |  
|-----|------------|  
| CLI MVP | Entièrement fonctionnel |  
| Version web | FastAPI / Flask + React |  
| Marché secondaire | DEX par-dessus les jetons |  
| Blockchain | Émission via contrats intelligents |  
| DAO | Vote sur le développement de l’entreprise |  
| Marché mondial | Support de plusieurs pays |  
---
## 📉 21. Risques et mesures d’atténuation  
| Risque | Solution |  
|------|----------|  
| Complexités juridiques | Fonctionnement via SPV dans des juridictions régulées |  
| Fraude financière | Vérification via Open Banking |  
| Données incorrectes sur les revenus | Utilisation d’oracles |  
| Dépendance à une seule API | Ajout de données factices et d’autres API |  
| Barrière d’entrée élevée | Investissement minimum — 100 $ |  
| Sortie de l’investisseur | Marché secondaire des jetons |  
| Perte de clé / compte | Phrases de récupération, restauration par email |  
| Pannes techniques | Sauvegarde de la base de données, sauvegardes |  
| Fraude de l’entreprise | Vérification via API et documents |  
| Répartition incorrecte des dividendes | Règles automatiques de calcul |  
| Manque de liquidité | Création de pools de liquidité et staking |  
| Changement de législation | Modèle flexible, fonctionnement via juridictions conformes |  
---
## 🧮 22. Formule des dividendes  
$$ \text{Dividende par jeton} = \frac{\text{Chiffre d'affaires de l'entreprise} \times \text{Part des dividendes}}{\text{Nombre total de jetons}} $$  
### Exemple :  
- Chiffre d’affaires : 10 000 $  
- Part des dividendes : 10 %  
- Jetons : 10 000  
$$ \text{Dividende par jeton} = \frac{10 000 \times 0,1}{10 000} = 0,10\ \text{$ par jeton} $$  
---
## 📊 23. Exemple de ROI pour un investisseur  
| Paramètre | Valeur |  
|----------|----------|  
| Jetons achetés | 1 000 |  
| Prix du jeton | 0,10 $ |  
| Montant total | 100 $ |  
| Dividendes mensuels | 10 $ |  
| Durée de détention | 12 mois |  
| Dividendes totaux | 120 $ |  
| Prix du jeton après 1 an | 0,20 $ |  
| Recette de vente | 200 $ |  
| ROI total | **220 % sur un an** |  
---
## 📊 24. Exemple : croissance de l’entreprise et hausse du prix du jeton  
| Mois | Chiffre d’affaires | % de dividendes | Prix du jeton |  
|-------|--------|--------------|-------------|  
| 1     | 10 000 $ | 10 %          | 0,10 $       |  
| 3     | 12 000 $ | 10 %          | 0,12 $       |  
| 6     | 15 000 $ | 10 %          | 0,15 $       |  
| 9     | 18 000 $ | 10 %          | 0,18 $       |  
| 12    | 20 000 $ | 10 %          | 0,20 $       |  
👉 Le jeton a augmenté de 100 % en valeur, et les dividendes ont assuré un revenu stable.  
---
## 📌 25. Pourquoi cela intéresse-t-il l’investisseur ?  
- ✔️ **Les RWA deviennent l’un des secteurs les plus dynamiques de la DeFi**  
- ✔️ **Les petites entreprises représentent un marché énorme et sous-évalué**  
- ✔️ **La répartition automatique des bénéfices assure une forte liquidité**  
- ✔️ **Possibilité de démarrer en Russie, puis de s’étendre au monde entier**  
---
## 📦 26. Que peut-on ajouter ensuite ?  
| Fonction | Description |  
|---------|----------|  
| **Jetons sous forme de NFT** | Droits uniques aux dividendes |  
| **Gouvernance DAO** | Vote sur le développement de l’entreprise |  
| **Graphiques de rendement** | Pour analyse et sélection |  
| **Support multi-devises** | RUB, USD, USDT, USDC |  
| **Rachat automatique de jetons** | L’entreprise peut racheter ses propres jetons |  
| **Assurance des jetons** | Protection contre la faillite |  
| **Intégration blockchain** | Pour sécurité et transparence |  
---
## 📈 27. Parcours de développement du jeton  
```
Émission → Vente primaire → Croissance de l’entreprise → Hausse du prix → Marché secondaire → Sortie de l’investisseur
```
---
## 📊 28. Jetons comme actions de petites entreprises  
| Paramètre | TokenizeLocal |  
|----------|--------------|  
| Dividendes | Oui, mensuels |  
| Participation au capital | Oui, via jetons |  
| Marché secondaire | Prévu |  
| Revenu passif | Oui |  
| Décentralisation | Prévue via blockchain |  
| Risque | Modéré, l’entreprise peut être vérifiée |  
| ROI | 10–20 % par mois (selon l’entreprise) |  
---
## ✨ 29. Proposition de valeur unique  
| Ce que nous faisons | Ce qui nous distingue |  
|-----------|----------------|  
| Tokenisation d’entreprises | Pas seulement de gros actifs, mais aussi cafés, distributeurs, énergie solaire |  
| Modèle centralisé | Lancement rapide, peu coûteux |  
| Paiement de dividendes | Proportionnel aux jetons détenus |  
| Prêt pour la blockchain | Possibilité de passer sur Polygon / TON |  
| Convivialité pour l’investisseur | Consultation des jetons et dividendes |  
---
## 📈 30. Conclusion  
> **TokenizeLocal** est la première plateforme permettant aux petites entreprises de lever des fonds via la tokenisation.  
> Les investisseurs obtiennent :  
> - Des dividendes chaque mois  
> - Une possibilité d’appréciation du prix du jeton  
> - La possibilité de revendre  
> L’entreprise obtient :  
> - Un financement sans intérêts bancaires  
> - Un accès mondial aux investisseurs  
> - Un modèle flexible avec options de contrôle  
---