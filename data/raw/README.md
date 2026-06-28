# Raw Synthetic Source Data

This directory is the default output location for generated RenewalOS synthetic raw CSV files.

Generate the files with:

```powershell
renewalos-generate-raw
```

The generated CSV files are synthetic and intentionally include controlled data-quality incidents from the documented failure scenarios. They are raw source files only and must not be used directly for management KPI reporting.

Generated CSV files are ignored by Git. Keep the generation code, tests, and documentation under version control instead.
