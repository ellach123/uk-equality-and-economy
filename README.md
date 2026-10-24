# Women in Management & the Creative Economy

**How do social equality and economic development relate across England & Wales?**
A visual analytics project on 323 local authorities, linking the **2011** and **2021** UK Censuses in Tableau.

## Contents

| Part | Status |
|---|---|
| [**Version 1 · Original analysis**](v1-original/) — a Tableau Story with eight dashboards on gender equality, ethnic diversity and the creative, education and wider industries | Available |
| **Version 2 · Revisited analysis** — the same question, measured with rates and shares | In progress |
| **Comparison** — how the two versions differ, step by step | In progress |

## Repository structure

```
├── README.md          overview (this page)
├── data/              census extracts and the merged dataset
└── v1-original/       version 1: README, Tableau workbook, data preparation notebook
```

## Data

[Office for National Statistics, Census 2011 and Census 2021](https://www.ons.gov.uk/census), local-authority level for England & Wales, used under the [Open Government Licence v3.0](https://www.nationalarchives.gov.uk/doc/open-government-licence/version/3/). UK geocoding in the Tableau workbook is from The Information Lab.

| Folder / file | Contents |
|---|---|
| `data/2011_industry_by_sex/`, `data/2011_occupation_by_sex/` | 2011 industry and occupation, total and by sex |
| `data/2021_industry/`, `data/2021_occupation/`, `data/2021_Ethnic_groups/` | 2021 industry, occupation and ethnic group |
| `data/data_selected_for_tableau.csv` | Merged dataset used in Tableau |
| `data/pca_projected_data.csv`, `data/tsne_projected_data.csv` | PCA and t-SNE projections |
