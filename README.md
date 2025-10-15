# Bunny_CDN
## Modify requirements.txt <br>
<br>
Pillow>=10.0.0,<11 <br>
&emsp;pip install pillow <br>
pillow_heif>=0.10.0 <br>
&emsp;pip install pillow-heif

## Modify settings.py
BUNNY_STORAGE_ZONE  &emsp;      = &emsp; config("BUNNY_STORAGE_ZONE") <br>
BUNNY_STORAGE_PASSWORD &emsp;   = &emsp;config("BUNNY_STORAGE_PASSWORD")<br>
BUNNY_STORAGE_ENDPOINT  &emsp;  = &emsp;config("BUNNY_STORAGE_ENDPOINT")<br>
BUNNY_CDN_BASE_URL     &emsp;   = &emsp;config("BUNNY_CDN_BASE_URL")<br>
BUNNY_PULL_ZONE_ID     &emsp;   =&emsp; int(config("BUNNY_PULL_ZONE_ID", "0"))<br>
BUNNY_API_KEY     &emsp;        = &emsp;config("BUNNY_API_KEY")<br>
BUNNY_OPTIMIZER_DEFAULTS &emsp; =&emsp; config("BUNNY_OPTIMIZER_DEFAULTS", "auto_optimize=medium")<br>
BUNNY_PURGE_ON_OVERWRITE &emsp; =&emsp; config("BUNNY_PURGE_ON_OVERWRITE", "true").lower() == "true"<br>

Note:- Make sure the credentials are saved in .env file

## CDN

Create a new folder named “CDN” with the following structure <br>

CDN <br>
&emsp;├── init.py<br>
&emsp;└── image_utils.py<br>
&emsp;└── bunny.py<br>
&emsp;└── image_utils.py<br>
&emsp;└── helpers.py<br>
