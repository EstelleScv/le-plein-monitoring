# ⚡ Dashboard Monitoring Le Plein

Dashboard interactif pour le monitoring des bornes de recharge Le Plein, connecté à MotherDuck.

## 🚀 Démo en ligne

L'app est déployée sur Streamlit Cloud : [Accéder au dashboard](#)

## 📊 Fonctionnalités

- 📈 **KPI en temps réel** : Sessions, Part de marché, Clients, Énergie
- 🎨 **Graphiques interactifs** : Sessions par enseigne, PDM, Mix de puissance
- 📋 **Tableau détaillé** : Données par site avec tri et filtres
- 📥 **Export CSV** : Télécharge les données
- 🔄 **Filtres dynamiques** : Sélection par mois

## 🛠️ Technologies

- **Streamlit** - Framework web Python
- **MotherDuck** - Data warehouse (DuckDB cloud)
- **Plotly** - Visualisations interactives
- **Pandas** - Manipulation de données

## 🔒 Sécurité

Ton token MotherDuck reste privé :
- Stocké uniquement dans ta session navigateur
- Jamais committé dans Git
- Jamais visible par d'autres utilisateurs

## 📝 Installation locale (optionnel)

```bash
# Clone le repo
git clone https://github.com/TON-USERNAME/le-plein-monitoring.git
cd le-plein-monitoring

# Installe les dépendances
pip install -r requirements.txt

# Lance l'app
streamlit run app_streamlit.py
```

## 🔑 Configuration

1. Obtiens ton token MotherDuck sur https://app.motherduck.com (Settings → Tokens)
2. Lance l'app
3. Colle ton token dans la barre latérale
4. Sélectionne un mois et clique sur "Actualiser"

## 📧 Contact

Pour toute question, contacte [ton-email]
