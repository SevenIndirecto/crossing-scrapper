# Cro - Slo Border Crossing Scrapper

The scrapper project consists of a python scrapper and vue visualizer

## Local instance / development

### Scrapper

Setup env with [poetry](https://python-poetry.org/)

1. `poetry shell` This will create a virtual env
2. `cp cron.sample.py cron.py`, make it executable `chmod +x cron.py` and update the shebang path.
    You can get get the path by running `poetry env info`
3. 

Run `cron.sample.py`

### Visualizer

```
# install dependencies
yarn
# run hot reload build
yarn serve
```

## Production

## Setting up the scrapper

Setup a cron job to run the scrapper periodically. A cron.sample.py file is provided.

1. 
2. 
3. 

Example cron entry:

```
0,30 * * * * `/some/path/scrapper/cron.py`
```


## Setting up the visualizer

1. Run `yarn build`
2. Copy content of `dist` to a webserver
3. On webserver link the scrapper's history file to the root of the webserver files

Example:

You're serving files from `/srv/scrapper-web/` and your `history.json` file is located in `/home/history.json`.
Sym link the file: `ln -s /home/history.json /srv/scrapper-web/history.json`.
