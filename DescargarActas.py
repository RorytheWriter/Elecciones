import boto3
import json
import requests
import os
from requests_aws4auth import AWS4Auth
from datetime import datetime as dt

print("\n===============\n Hola! Ten a la mano la página de la Registraduría para confirmar los códigos del Departamento y Municipio deseados.")
dep=input("Ingresa Departamento (DOS (2) dígitos, ej 03): ").strip()
assert len(dep)==2, f"Código de departamento errado {dep}"
mun=input("Ingresa Municipio (TRES (3) dígitos, ej 052):").strip()
assert len(mun)==3, f"Código de municipio errado {mun}"
# dep="03" # ATLANTICO
# mun="052" # SOLEDAD

REGION = "us-east-2"
IDENTITY_POOL_ID = "us-east-2:b3d8591c-b2ce-40b6-a96c-550c26f7bfd9"

client = boto3.client("cognito-identity", region_name=REGION)
identity_resp = client.get_id(IdentityPoolId=IDENTITY_POOL_ID)
identity_id = identity_resp["IdentityId"]

creds_resp = client.get_credentials_for_identity(IdentityId=identity_id)
creds = creds_resp["Credentials"]

# print(identity_id)
# print(creds["AccessKeyId"])
# print(creds["SecretKey"])
# print(creds["SessionToken"])

REGION = "us-east-2"
SERVICE = "appsync"
GRAPHQL_URL = "https://apx2e14awsprodcong.tps.net.co/graphql"

awsauth = AWS4Auth(
    creds["AccessKeyId"],
    creds["SecretKey"],
    REGION,
    SERVICE,
    session_token=creds["SessionToken"]
)

## DESCARGAR JSON DE CODIGOS
def download_transmcodes():
    txcodesurl="https://divulgacione14presidente.registraduria.gov.co/assets/temis/divipol_json/allTransmissionCodes.json"
    codes_headers={
        "user-agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/149.0.0.0 Safari/537.36",
        "accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.7",
        "authority": "divulgacione14presidente.registraduria.gov.co",
        "accept-encoding": "gzip, deflate, br, zstd",
        "get":"GET",
        "Referer":f"https://divulgacione14presidente.registraduria.gov.co/departamento/{dep}",        
        "sec-fetch-dest": "document",
        "sec-fetch-mode": "navigate",
        "sec-fetch-site": "none",
    }
    r = requests.get(txcodesurl, headers=codes_headers, timeout=10, allow_redirects=True)
    r.raise_for_status()
    if "json" not in r.headers.get("content-type", "").lower():
            raise RuntimeError(f"No devolvió JSON: {r.headers.get('content-type')}")
    with open("allTransmissionCodes.json", "wb") as f:
        f.write(r.content)

print("Se descargó la lista de códigos (allTransmissionCodes.json).")
download_transmcodes()


## PARSE JSON DE CODIGOS 
with open("allTransmissionCodes.json", encoding="utf-8") as f:
    data = json.load(f)["data"]

def iter_nodes(obj):
    for status in obj.values():
        nodes = status.get("nodes", [])

        for chunk in nodes:
            if isinstance(chunk, dict):
                yield chunk

            elif isinstance(chunk, list):
                yield from chunk

def filtrar(obj, dep, mun):
    for node in iter_nodes(obj):

        if (
            node.get("idDepartmentCode") == dep
            and node.get("municipalityCode") == mun
        ):
            yield {
                "dep": node.get("idDepartmentCode"),
                "mun": node.get("municipalityCode").zfill(3),
                "zona": node.get("idZoneCode").zfill(3),
                "puesto": node.get("standCode"),
                "mesa": node.get("numberStand"),
                "expected_name": node.get("expectedName"),
            }

resultados=list(filtrar(data, dep, mun))
hora=dt.now().strftime("%H-%M")
print(f"{len(resultados)} actas encontradas. Descargando a las {hora}")

### DESCARGAR PDFS
os.makedirs("pdf", exist_ok=True)

def build_pdf_url(dep, mun, zona, puesto, mesa, corp_text, expected_name):
    return (
        "https://divulgacione14presidente.registraduria.gov.co"
        f"/assets/temis/pdf/{dep}/{mun}/{zona}/{puesto}/{mesa}/{corp_text}/{expected_name}"
    )

def download_pdf(url, path):
    headers={
        "user-agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/149.0.0.0 Safari/537.36",
        "accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.7",
        "authority": "divulgacione14presidente.registraduria.gov.co",
        "get":"GET",
        "accept-encoding": "gzip, deflate, br, zstd",
        "accept-language": "en-GB,en;q=0.9,en-US;q=0.8,es;q=0.7,zh-CN;q=0.6,zh;q=0.5,es-MX;q=0.4",
        "cache-control": "max-age=0"
    }
    r = requests.get(url, headers=headers, timeout=10, allow_redirects=True)
    r.raise_for_status()
    if "pdf" not in r.headers.get("content-type", "").lower():
        raise RuntimeError(f"No devolvió PDF: {r.headers.get('content-type')}")
    with open(path, "wb") as f:
        f.write(r.content)

for el in resultados:
    dep=el["dep"]
    mun=el["mun"]
    zona=el["zona"]
    puesto=el["puesto"]
    mesa=el["mesa"]
    pdfname=el["expected_name"]
    corp="PRE"

    pathname=f"Dep{dep}-Mun{mun}-Zona{zona}-Puesto{puesto}-Mesa{mesa}-T{hora}_{pdfname}.pdf"
    print(f"Descargando Zona {zona} - Puesto {puesto} - Mesa {mesa}")
    download_pdf(build_pdf_url(dep,mun,zona,puesto,mesa,corp,pdfname),f"pdf/{pathname}")

print("====FINALIZADO====")