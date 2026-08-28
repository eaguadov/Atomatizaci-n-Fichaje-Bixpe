"""Test rápido para verificar que el sistema de festivos funciona correctamente.
Simula lo que hace el bot cada mañana: descarga team_holidays.json y comprueba
si hoy (o una fecha concreta) es festivo para un empleado dado.

Uso:
  python scripts/test_festivos.py Eusebio
  python scripts/test_festivos.py Eusebio 2026-12-25
  python scripts/test_festivos.py Antonio 2027-01-01
"""
import sys
import json
import urllib.request
from datetime import date, datetime

URL = "https://raw.githubusercontent.com/eaguadov/Atomatizaci-n-Fichaje-Bixpe/main/team_holidays.json"

def main():
    if len(sys.argv) < 2:
        print("Uso: python scripts/test_festivos.py <NOMBRE> [FECHA yyyy-mm-dd]")
        print("Ejemplo: python scripts/test_festivos.py Eusebio 2026-12-25")
        return

    empleado = sys.argv[1].strip()
    fecha_test = sys.argv[2].strip() if len(sys.argv) > 2 else date.today().strftime("%Y-%m-%d")

    print("=" * 56)
    print("  TEST DE FESTIVOS - Simulador del Bot")
    print("=" * 56)
    print(f"\n  Empleado:     {empleado}")
    print(f"  Fecha a comprobar: {fecha_test}")

    # 1. Descargar calendario maestro
    print(f"\n  Descargando team_holidays.json desde GitHub...")
    try:
        req = urllib.request.Request(URL)
        with urllib.request.urlopen(req, timeout=10) as response:
            team_data = json.loads(response.read().decode('utf-8'))
    except Exception as e:
        print(f"  ERROR al descargar: {e}")
        return

    # 2. Buscar empleado
    if empleado not in team_data:
        nombres = ", ".join(team_data.keys())
        print(f"\n  RESULTADO: El empleado '{empleado}' NO existe en el calendario.")
        print(f"  Empleados disponibles: {nombres}")
        return

    emp_data = team_data[empleado]
    total = len(emp_data)
    print(f"  Encontrado. {empleado} tiene {total} dias registrados.")

    # 3. Comprobar fecha
    if isinstance(emp_data, dict):
        if fecha_test in emp_data:
            motivo = emp_data[fecha_test]
            print(f"\n  RESULTADO: {fecha_test} ES festivo/vacacion para {empleado}.")
            print(f"  Motivo: {motivo}")
            print(f"\n  >>> El bot NO ficharia este dia. <<<")
        else:
            print(f"\n  RESULTADO: {fecha_test} es un dia LABORABLE para {empleado}.")
            print(f"\n  >>> El bot SI ficharia este dia. <<<")
    elif isinstance(emp_data, list):
        if fecha_test in emp_data:
            print(f"\n  RESULTADO: {fecha_test} ES festivo/vacacion para {empleado}.")
            print(f"\n  >>> El bot NO ficharia este dia. <<<")
        else:
            print(f"\n  RESULTADO: {fecha_test} es un dia LABORABLE para {empleado}.")
            print(f"\n  >>> El bot SI ficharia este dia. <<<")

    # 4. Mostrar próximos festivos
    print(f"\n  --- Proximos festivos de {empleado} ---")
    if isinstance(emp_data, dict):
        futuros = {k: v for k, v in emp_data.items() if k >= fecha_test}
        for f, m in list(sorted(futuros.items()))[:10]:
            print(f"    {f}  ({m})")
        if len(futuros) > 10:
            print(f"    ... y {len(futuros) - 10} mas.")
    elif isinstance(emp_data, list):
        futuros = [f for f in sorted(emp_data) if f >= fecha_test]
        for f in futuros[:10]:
            print(f"    {f}")

    print("\n" + "=" * 56)

if __name__ == "__main__":
    main()
