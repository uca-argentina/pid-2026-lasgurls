# Comandos

## Traer la branch PARCIAL

Si todavia no clonaste el repo:

```bash
git clone -b PARCIAL https://github.com/uca-argentina/pid-2026-lasgurls.git
cd pid-2026-lasgurls
```

Si ya lo tenias clonado:

```bash
cd pid-2026-lasgurls
git fetch origin
git switch PARCIAL
git pull
```

Para ver en que branch estas: `git branch`

## Crear tu branch a partir de PARCIAL

```bash
git switch -c caro-parcial
```

## Subir tus cambios

```bash
git add .
git commit -m "Descripcion de lo que hiciste"
git push -u origin caro-parcial
```

## Ver la base de datos

```bash
cd pid-2026-lasgurls
sqlite3 juntapp.db
.tables
.schema juntadas
.quit
```

## Correr los tests

```bash
python3 -m pytest tests -q
```

## Armar la base local

```bash
python3 -m base_datos.preparar_local
```

## Correr la app

```bash
python3 app.py
```
## limpiar

```
lsof -ti:5001 | xargs kill -9

```