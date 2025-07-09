# ch-java (pour Windows)

**Note:** Ce script (`ch.bat`) est un utilitaire simple pour les utilisateurs de Windows souhaitant changer rapidement de version de JDK via la ligne de commande. Pour un gestionnaire de versions Java multi-plateforme plus complet, voir la documentation de [jenv (README.md)](README.md).

## Qu’est-ce que c’est ?

Change la version java avec une simple commande car jongler avec les différentes versions de Java peut être un vrai casse-tête. 
## Pourquoi ce script est-il indispensable ?

Vous avez plusieurs versions de Java installées sur votre machine ? Vous passez votre temps à changer de version à chaque projet vraiment ? voici la solution donc 

- **Changer de version Java ?**
- **Lister toutes les versions installées ?**
- **Mettre à jour les variables d’environnement ?**

## Comment l’utiliser ?

### 1. Lancer sur votre terminal

```bash
curl -o ch.bat https://raw.githubusercontent.com/traorecheikh/ch-jdk-changer/refs/heads/main/ch.bat && echo "Merci <3 ! Utilisez 'ch help' pour voir les commandes disponibles. Reouvrir le terminal aussi."
```

- **lancez ch -v sur le terminal ensuite vous fermer le terminal et ouvrez un nouveau**
### 2. Utiliser les commandes

- **Lister les versions de Java :**

```bash
ch list
```

- **Changer de version Java :**

```bash
ch global 17
```

- **Besoin d’aide ?** C’est facile :

```bash
ch help
```

## Pourquoi c’est cool ?

Parce que gerer les versions de Java, c'est chiant. ch jdk rend les choses simples. Vous n’avez pas besoin de chercher dau fin fond de votre terminal ou d’essayer de vous rappeler quelle version de Java correspond à quel projet. Vous indiquez juste la version, et hop, tout est configuré.

## Contribution

Vous avez une idée nulle ou un bug (garder pour vous franchement ) ? Ouvrez une PR, c’est pas la mer à boire. 

## Licence

C’est open-source, donc vous pouvez faire ce que vous--- (ou presque). Voir [LICENSE](LICENSE).

---
