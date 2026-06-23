import json
import requests
import os
from datetime import datetime as dt

print("\n===============\n Hola! Ten a la mano la página de la Registraduría para confirmar los códigos del Departamento (y Municipio) deseados.")
dep=input("Ingresa Departamento (DOS (2) dígitos, ej 03) y presiona ENTER: ").strip()
assert len(dep)==2, f"Código de departamento errado {dep}"
mun=input("Ingresa Municipio (TRES (3) dígitos, ej 052) y presiona ENTER. Si quieres descargar TODO el departamento, sólo presiona ENTER:").strip()
if len(mun)==0:
    mun=None
else:
    assert len(mun)==3, f"Código de municipio errado {mun}"
cual=int(input("Cual de los formularios vas a descargar? Elige una de las opciones:\n1 - Delegados\n2 - Transmisión\n3 - Claveros\n").strip())
assert int(cual) and cual in {1,2,3}, f"Opción errada {cual}"
# dep="03" # ATLANTICO
# mun="052" # SOLEDAD

def download_file(url, path, filetype,headers,timeout=60):
    r = requests.get(url, headers=headers, timeout=timeout, allow_redirects=True)
    r.raise_for_status()
    ret_head=r.headers.get("content-type", "").lower()
    if filetype not in ret_head and "octet-stream" not in ret_head:
        raise RuntimeError(f"No devolvió {filetype}: {ret_head}")
    with open(path, "wb") as f:
        f.write(r.content)

## DELEGADOS Y TRANSMISION ES PARECIDO
if cual in {1,2}:
    # txcodesurl="https://divulgacione14presidente.registraduria.gov.co/assets/temis/divipol_json/allTransmissionCodes.json" #PRIMERA VUELTA
    ## DESCARGAR JSON DE CODIGOS


    match cual:
            case 1: # Delegados
                txcodesurl="https://e14segundavueltapresidente.registraduria.gov.co/assets/temis/divipol_json/allTransmissionCodes.json"
            case 2: # Transmision
                txcodesurl="https://e14segundavueltapresidentet.registraduria.gov.co/assets/temis/divipol_json/allTransmissionCodes.json"
    codes_headers={
            "user-agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/149.0.0.0 Safari/537.36",
            "accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.7",
            "authority": f"e14segundavueltapresidente{"t" if cual==2 else ""}.registraduria.gov.co",
            "accept-encoding": "gzip, deflate, br, zstd",
            "get":"GET",
            "Referer":f"https://e14segundavueltapresidente{"t" if cual==2 else ""}.registraduria.gov.co/departamento/{dep if dep is not None else "01"}",        
            # "Referer":f"https://divulgacione14presidente.registraduria.gov.co/departamento/{dep}",  #PRIMERA VUELTA
            "sec-fetch-dest": "empty",
            "sec-fetch-mode": "cors",
            "sec-fetch-site": "none",
            "connection": "keep-alive"
        }
    download_file(txcodesurl,"allTransmissionCodes.json","json",codes_headers)
    print("Se descargó la lista de códigos (allTransmissionCodes.json).")


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
                and (mun is None or node.get("municipalityCode") == mun)
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
    print(f"{len(resultados)} actas encontradas.")

    ### DESCARGAR PDFS
    os.makedirs("pdf", exist_ok=True)

    def build_pdf_url(dep, mun, zona, puesto, mesa, corp_text, expected_name):
        return (
            # "https://divulgacione14presidente.registraduria.gov.co"
            f"https://e14segundavueltapresidente{"t" if cual==2 else ""}.registraduria.gov.co/assets/temis/pdf/{dep}/{mun}/{zona}/{puesto}/{mesa}/{corp_text}/{expected_name}"
        )

    for el in resultados:
        dep=el["dep"]
        mun=el["mun"]
        zona=el["zona"]
        puesto=el["puesto"]
        mesa=el["mesa"]
        pdfname=el["expected_name"]
        corp="PRE"
        hora=dt.now().strftime("%H-%M")

        pathname=f"Dep{dep}-Mun{mun}-Zona{zona}-Puesto{puesto}-Mesa{mesa}-{"Deleg" if cual==1 else "Trans"}-T{hora}_{pdfname}.pdf"
        print(f"Descargando Mun {mun} - Zona {zona} - Puesto {puesto} - Mesa {mesa}")
        
        headers={
            "user-agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/149.0.0.0 Safari/537.36",
            "accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.7",
            "authority": f"e14segundavueltapresidente{"t" if cual==2 else ""}.registraduria.gov.co",
            # "authority": "divulgacione14presidente.registraduria.gov.co",
            "get":"GET",
            "accept-encoding": "gzip, deflate, br, zstd",
            "accept-language": "en-GB,en;q=0.9,en-US;q=0.8,es;q=0.7,zh-CN;q=0.6,zh;q=0.5,es-MX;q=0.4",
            "cache-control": "max-age=0",
            "connection": "keep-alive"
        }
        download_file(build_pdf_url(dep,mun,zona,puesto,mesa,corp,pdfname),f"pdf/{pathname}","pdf",headers)

####################

## CLAVEROS ES DISTINTO
elif cual==3:
    baseurl="https://escrutinios2vueltapresidente2026.registraduria.gov.co"
    # Obtener mesas por dept/mun
    print("Descargando datos de divipol")
    download_file(f"{baseurl}/data/esc/v1/divipole/divipole_20260609_095453_471.json",
                  "divipole_20260609_095453_471.json",
                  "json",
                  {"user-agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/149.0.0.0 Safari/537.36",
                    "authority": "escrutinios2vueltapresidente2026.registraduria.gov.co",
                   })
    with open("divipole_20260609_095453_471.json", encoding="utf-8") as f:
        data_divipole = json.load(f)

    def filtrar_divipol():
        if mun is not None:
            municipios = {mun: data_divipole["departamentos"][dep]["municipios"][mun]}
        else:
            municipios = data_divipole["departamentos"][dep]["municipios"]
        return set(municipios.keys())
        
        # no need dict, use plain set, dont need data
        # for mun_cod, mun_data in municipios.items():
        #     mun_puestos[mun_cod]=mun_data
            # fuck list of dicts
            # for zona_cod, zona_data in mun_data["zonas"].items():
                # for puesto_cod in zona_data["puestos"].keys():
                    # puestos.append({
                    #     "dep": dep,
                    #     "mun": mun_cod,
                    #     "zona": zona_cod,
                    #     "puesto": puesto_cod,
                    # })
        # return mun_puestos
    municipios=filtrar_divipol()
    # print(mun_puestos)
    
    # Obtener index.json
    print("Recopilando nombres de archivos")
    download_file(f"{baseurl}/data/index.json",
                  "index.json",
                  "json",
                  {"user-agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/149.0.0.0 Safari/537.36",
                    # "authority": "escrutinios2vueltapresidente2026.registraduria.gov.co",
                "Referer": "https://escrutinios2vueltapresidente2026.registraduria.gov.co/actas-e14",
                "Connection": "keep-alive",
                "Sec-Fetch-Dest": "empty",
                "Sec-Fetch-Mode": "cors",
                "Sec-Fetch-Site": "same-origin"

                   })
    with open("index.json", encoding="utf-8") as f:
        index = json.load(f)

    for key,val in index.items():
        if not key.endswith("/mesas/"): continue
        # ej:
        # k: data/esc/v1/actas-documentos/001/01/070/01/04/mesas/
        # v: actas_documentos_001_01_070_01_04_mesas_20260621_174823_819.json
        parts = key.strip("/").split("/")
        # Siempre misma estructura
        departamento = parts[5]  # 01
        municipio    = parts[6]  # 070
        zona         = parts[7]  # 01
        puesto       = parts[8]  # 04

        # filtro por municipios
        if not departamento==dep: continue
        if municipio not in municipios: continue   
        
        print(f"=== Mun {municipio} - Zona {zona} - Puesto {puesto} ===")
        # print(key)
        # print(parts)  
        
        url_json_puesto = baseurl+"/"+key+val
        r = requests.get(
            url_json_puesto,
            headers={"user-agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/149.0.0.0 Safari/537.36",
                    "authority": "escrutinios2vueltapresidente2026.registraduria.gov.co",
                     },
            timeout=60,
            allow_redirects=True
        )
        r.raise_for_status()
        json_puesto = r.json()
        
        for m in json_puesto:
            mesa = m["numero"]            
            nombre = m["nombre_archivo"]
            # nom es ej: /docs/E14/03/052/05/02/E14_PRE_03_052_005_00_02_001_5391.pdf
            hora=dt.now().strftime("%H-%M")

            headers={
            "user-agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/149.0.0.0 Safari/537.36",
                    "authority": "escrutinios2vueltapresidente2026.registraduria.gov.co",
            "connection": "keep-alive",
            "accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.7",
            "sec-fetch-dest": "empty",
            "sec-fetch-mode": "cors",
            "sec-fetch-site": "same-origin",
            "accept-encoding": "identity",
            "scheme":"https",
            "Sec-GPC":"1",
            "Referer":"https://escrutinios2vueltapresidente2026.registraduria.gov.co/actas-e14",
            "Priority":"u=4",
            "DNT":"1"
            }

            # print(f"Descargando Mun {mun} - Zona {zona} - Puesto {puesto} - Mesa {mesa}\n de {nombre}")
            print(f"Descargando Mun {municipio} - Zona {zona} - Puesto {puesto} - Mesa {mesa}")
            pathname=f"Dep{dep}-Mun{municipio}-Zona{str(zona).zfill(3)}-Puesto{puesto}-Mesa{str(mesa).zfill(3)}-Clav-T{hora}.pdf"
            # print(f"https://escrutinios2vueltapresidente2026.registraduria.gov.co{nombre}")
            download_file(f"https://escrutinios2vueltapresidente2026.registraduria.gov.co{nombre}",f"pdf/{pathname}","pdf",headers)

print("====FINALIZADO====")