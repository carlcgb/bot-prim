# 🤖 Guide d'utilisation de PRIMBOT - Obtenir les meilleures réponses

## 🎯 Améliorations récentes

PRIMBOT a été amélioré pour fournir des réponses **plus détaillées et utiles pour le débogage** :

### ✨ Nouvelles fonctionnalités

1. **Recherche étendue** : Recherche dans 10 documents au lieu de 5 pour un meilleur contexte
2. **Scores de pertinence** : Affiche la pertinence de chaque résultat (🟢 Très pertinent, 🟡 Pertinent, etc.)
3. **Réponses structurées** : Réponses organisées avec titres, listes, et sections claires
4. **Détails techniques** : Inclus les noms de champs, valeurs, chemins, et exemples concrets
5. **Citations de sources** : Mentionne toujours les URLs de documentation utilisées
6. **Diagnostic amélioré** : Propose des étapes de diagnostic si le problème n'est pas clair
7. **Plus d'images** : Affiche jusqu'à 8 captures d'écran au lieu de 5

## 💡 Comment obtenir les meilleures réponses

### 1. **Soyez spécifique dans vos questions**

❌ **Mauvais** : "Ça ne marche pas"
✅ **Bon** : "Erreur lors de l'export CSV : le champ 'Date facturation' est vide"

❌ **Mauvais** : "Comment faire un client ?"
✅ **Bon** : "Procédure détaillée pour créer un nouveau client avec tous les champs obligatoires"

### 2. **Utilisez des termes techniques**

L'agent recherche dans la documentation technique, utilisez :
- Noms de champs exacts
- Codes d'erreur
- Noms de fonctionnalités
- Termes de la documentation PrimLogix

**Exemples de bonnes requêtes** :
- "Configuration du champ 'Numéro de facture' dans les paramètres"
- "Résolution erreur E001 lors de la sauvegarde"
- "Export des données clients au format Excel avec filtres"

### 3. **Posez des questions de diagnostic**

Si vous avez un problème, demandez :
- "Quelles sont les causes possibles de [problème] ?"
- "Étapes de diagnostic pour [symptôme]"
- "Vérifications à faire avant [action]"

### 4. **Demandez des détails spécifiques**

L'agent peut maintenant fournir :
- **Exemples concrets** : "Montre-moi un exemple de configuration pour..."
- **Procédures étape par étape** : "Procédure complète pour..."
- **Comparaisons** : "Différence entre [option A] et [option B]"
- **Dépannage** : "Comment résoudre [erreur spécifique]"

## 📊 Comprendre les résultats de recherche

Quand l'agent recherche dans la base de connaissances, vous verrez :

### Scores de pertinence

- 🟢 **Très pertinent (80-100%)** : Résultat très proche de votre question
- 🟡 **Pertinent (60-79%)** : Résultat utile mais peut nécessiter du contexte
- 🟠 **Modérément pertinent (40-59%)** : Résultat partiellement lié
- ⚪ **Peu pertinent (<40%)** : Résultat faiblement lié

### Structure des réponses

Les réponses sont maintenant organisées ainsi :

```
📚 Résultats de recherche (requête: "...")
Trouvé X document(s) pertinent(s)...

### 📄 Document #1: [Titre] 🟢 [Très pertinent] (Score: 85%)
**URL:** https://...
**Chunk:** 2

**Contenu:**
[Contenu détaillé du document]

📊 Résumé: X document(s) trouvé(s), Y image(s) associée(s)
```

## 🔍 Exemples de questions efficaces

### Pour le débogage

```
"Erreur 'Champ obligatoire manquant' lors de la création d'une facture.
Quels sont les champs obligatoires et comment les vérifier ?"
```

### Pour comprendre une fonctionnalité

```
"Explication détaillée de la fonctionnalité 'Export multi-format'
avec exemples de configuration et captures d'écran"
```

### Pour une procédure complète

```
"Procédure étape par étape pour configurer l'import de données clients
depuis un fichier CSV, avec tous les paramètres nécessaires"
```

### Pour comparer des options

```
"Différence entre 'Export Excel' et 'Export CSV' dans PrimLogix,
avec avantages et cas d'usage pour chaque format"
```

## 🎨 Format des réponses améliorées

L'agent fournit maintenant :

1. **Introduction** : Contexte et objectif
2. **Solution principale** : Réponse directe à la question
3. **Détails techniques** : Informations spécifiques (champs, valeurs, chemins)
4. **Étapes numérotées** : Pour les procédures
5. **Exemples** : Code, configurations, ou valeurs concrètes
6. **Sources** : URLs de documentation citées
7. **Diagnostic** : Si applicable, étapes de vérification
8. **Images** : Captures d'écran de la documentation

## 🚀 Conseils avancés

### Utiliser plusieurs recherches

Si la première réponse n'est pas satisfaisante, l'agent peut :
- Faire des recherches complémentaires avec des variantes
- Combiner les informations de plusieurs sources
- Proposer des alternatives

### Questions de suivi

Après une première réponse, vous pouvez demander :
- "Peux-tu donner plus de détails sur [point spécifique] ?"
- "Y a-t-il d'autres méthodes pour [action] ?"
- "Quels sont les pièges à éviter avec [fonctionnalité] ?"

### Mode débogage

Pour des problèmes complexes, structurez votre question :
1. **Contexte** : "Je travaille sur [scénario]"
2. **Problème** : "Lorsque je [action], j'obtiens [erreur/comportement]"
3. **Question** : "Comment résoudre cela ?"

## 📝 Notes importantes

- L'agent répond en **français** par défaut
- Les réponses sont basées sur la **documentation PrimLogix officielle**
- Les captures d'écran proviennent de la documentation
- Les scores de pertinence aident à évaluer la fiabilité des résultats

## 🆘 Si vous n'obtenez pas de bonnes réponses

1. **Reformulez** avec des termes plus techniques
2. **Soyez plus spécifique** sur le problème ou la fonctionnalité
3. **Utilisez des codes d'erreur** ou noms de champs exacts
4. **Posez des questions de suivi** pour affiner la recherche
5. **Vérifiez les scores de pertinence** - si tous sont faibles, reformulez

---

**Dernière mise à jour** : Améliorations pour réponses détaillées et débogage
**Version** : 2.0 - Enhanced Debugging Mode

