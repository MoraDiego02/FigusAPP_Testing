import json
import os

def expandir_y_generar_album_final():
    base_dir = os.path.dirname(os.path.abspath(__file__))
    input_path = os.path.join(base_dir, "html", "album_panini_mundial_2026.json")
    output_path = os.path.join(base_dir, "html", "album_base_completo.json")

    with open(input_path, "r", encoding="utf-8") as f:
        data = json.load(f)

    grupos_expandidos = []

    # Banderas oficiales de los equipos del mundial 2026
    banderas = {
        "CZE": "🇨🇿", "MEX": "🇲🇽", "RSA": "🇿🇦", "KOR": "🇰🇷",
        "BIH": "🇧🇦", "CAN": "🇨🇦", "QAT": "🇶🇦", "SUI": "🇨🇭",
        "BRA": "🇧🇷", "HAI": "🇭🇹", "MAR": "🇲🇦", "SCO": "🏴󠁧󠁢󠁳󠁣󠁴󠁿",
        "AUS": "🇦🇺", "PAR": "🇵🇾", "TUR": "🇹🇷", "USA": "🇺🇸",
        "CUW": "🇨🇼", "ECU": "🇪🇨", "GER": "🇩🇪", "CIV": "🇨🇮",
        "JAP": "🇯🇵", "NED": "🇳🇱", "SWE": "🇸🇪", "TUN": "🇹🇳",
        "BEL": "🇧🇪", "EGY": "🇪🇬", "IRN": "🇮🇷", "NZL": "🇳🇿",
        "CPV": "🇨🇻", "KSA": "🇸🇦", "ESP": "🇪🇸", "URU": "🇺🇾",
        "FRA": "🇫🇷", "IRQ": "🇮🇶", "NOR": "🇳🇴", "SEN": "🇸🇳",
        "ALG": "🇩🇿", "ARG": "🇦🇷", "AUT": "🇦🇹", "JOR": "🇯🇴",
        "COL": "🇨🇴", "COD": "🇨🇩", "POR": "🇵🇹", "UZB": "🇺🇿",
        "CRO": "🇭🇷", "ENG": "🏴󠁧󠁢󠁥󠁮󠁧󠁿", "GHA": "🇬🇭", "PAN": "🇵🇦"
    }

    # Jugadores estrella precargados para hacerlo interactivo y de calidad
    estrellas = {
        "ARG": "Lionel Messi", "FRA": "Kylian Mbappé", "BRA": "Vinicius Jr", "POR": "Cristiano Ronaldo",
        "NOR": "Erling Haaland", "ENG": "Jude Bellingham", "ESP": "Lamine Yamal", "GER": "Florian Wirtz",
        "URU": "Federico Valverde", "COL": "Luis Díaz", "MEX": "Santiago Giménez", "USA": "Christian Pulisic",
        "CAN": "Alphonso Davies", "MAR": "Achraf Hakimi", "BEL": "Kevin De Bruyne", "ITA": "Gianluigi Donnarumma",
        "KOR": "Son Heung-min", "NED": "Virgil van Dijk", "CRO": "Luka Modrić", "EGY": "Mohamed Salah",
        "SEN": "Sadio Mané", "ALG": "Riyad Mahrez", "ECU": "Moisés Caicedo", "PAR": "Julio Enciso",
        "SWE": "Alexander Isak", "TUR": "Arda Güler", "UKR": "Artem Dovbyk", "NZL": "Chris Wood"
    }

    for grupo_data in data["grupos"]:
        selecciones_grupo = []
        for sel in grupo_data["selecciones"]:
            codigo = sel["codigo"]
            pais = sel["pais"]
            flag = banderas.get(codigo, "🏳️")

            # Estructurar la lista oficial de 20 figuritas para cada selección
            figuritas_lista = []
            
            # 1. Escudo
            figuritas_lista.append({
                "numero": f"{codigo}1",
                "nombre": f"Escudo {pais}",
                "posicion": "Escudo"
            })
            
            # 2. Foto Grupal
            figuritas_lista.append({
                "numero": f"{codigo}2",
                "nombre": f"Foto Grupal {pais}",
                "posicion": "Foto Grupal"
            })

            # 3. 18 Jugadores (03 al 20)
            for num in range(3, 21):
                jugador_nombre = ""
                posicion = ""
                
                # Precargar al jugador estrella de la selección en la posición 10
                if num == 10 and codigo in estrellas:
                    jugador_nombre = estrellas[codigo]
                    posicion = "Delantero" if codigo in ["ARG", "FRA", "BRA", "POR", "NOR", "ESP", "MEX", "SWE", "EGY", "SEN", "ALG"] else "Mediocampista"
                
                figuritas_lista.append({
                    "numero": f"{codigo}{num}",
                    "nombre": jugador_nombre,
                    "posicion": posicion
                })

            selecciones_grupo.append({
                "pais": pais,
                "codigo": codigo,
                "flag": flag,
                "total_figuritas": 20,
                "figuritas": figuritas_lista
            })

        grupos_expandidos.append({
            "grupo": grupo_data["grupo"],
            "selecciones": selecciones_grupo
        })

    # Crear el JSON final del album base completo
    album_completo = {
        "album": {
            "titulo": "Copa Mundial de la FIFA 2026™ - Álbum Oficial FigusAPP",
            "edicion": data["album"]["edicion"],
            "sedes": data["album"]["sedes"],
            "fecha_torneo": data["album"]["fecha_torneo"],
            "total_figuritas": 980, # 20 especiales + 48 selecciones * 20 figuritas = 980
            "secciones_especiales": data["secciones_especiales"]
        },
        "grupos": grupos_expandidos
    }

    with open(output_path, "w", encoding="utf-8") as f:
        json.dump(album_completo, f, indent=4, ensure_ascii=False)

    print(f"¡Base de datos unificada y expandida con éxito en '{output_path}'!")

if __name__ == "__main__":
    expandir_y_generar_album_final()
