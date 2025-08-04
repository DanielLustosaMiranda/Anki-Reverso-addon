import json
import subprocess

def run_cmd(command):
    try:
        result = subprocess.run(command, capture_output=True, text=True, check=True)
        return json.loads(result.stdout)

    except FileNotFoundError:
        print("❌ ERRO: O comando 'node' não foi encontrado. O Node.js está instalado e no PATH do sistema?")
    except subprocess.CalledProcessError as e:
        print(f"❌ ERRO: O script do scraper falhou com o código de saída {e.returncode}.")
        print(f"   Mensagem de erro do scraper: {e.stderr}")
    except json.JSONDecodeError:
        print("❌ ERRO: Falha ao decodificar a resposta JSON do scraper. A saída não foi um JSON válido.")
        print(f"   Saída recebida: {result.stdout}")

    return None
