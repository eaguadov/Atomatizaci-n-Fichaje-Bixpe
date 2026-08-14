import subprocess
import sys
import os

def run_test(name, command, expected_returncode):
    print(f"\n========================================================")
    print(f"🧪 EJECUTANDO TEST: {name}")
    print(f"Comando: {command}")
    print(f"========================================================")
    
    result = subprocess.run(command, shell=True, capture_output=True, text=True)
    
    print("--- STDOUT ---")
    print(result.stdout)
    if result.stderr:
        print("--- STDERR ---")
        print(result.stderr)
        
    print(f"Código de salida obtenido: {result.returncode} (Esperado: {expected_returncode})")
    
    if result.returncode == expected_returncode:
        print(f"✅ TEST PASADO: {name}")
        return True
    else:
        print(f"❌ TEST FALLIDO: {name}")
        return False

def main():
    if hasattr(sys.stdout, 'reconfigure'):
        sys.stdout.reconfigure(encoding='utf-8')
    if hasattr(sys.stderr, 'reconfigure'):
        sys.stderr.reconfigure(encoding='utf-8')
    print("🚀 INICIANDO SUITE DE PRUEBAS DE AUTOMATIZACIÓN BIXPE")
    
    # 1. Test de Simulación Normal (START con --simulate --force)
    test1_cmd = f'python src/bixpe_bot.py --action START --force --simulate'
    t1_ok = run_test("Simulación Normal (START - Modal Cancelado)", test1_cmd, expected_returncode=0)
    
    # 2. Test de Simulación de Error (Botón faltante con --test-missing-button --force)
    test2_cmd = f'python src/bixpe_bot.py --action START --force --test-missing-button'
    t2_ok = run_test("Simulación de Error (Botón no encontrado / Error diagnosticado)", test2_cmd, expected_returncode=1)
    
    print("\n========================================================")
    print("📊 RESUMEN FINAL DE LA SUITE DE PRUEBAS")
    print("========================================================")
    print(f"Test 1 (Simulación Normal): {'PASADO ✅' if t1_ok else 'FALLIDO ❌'}")
    print(f"Test 2 (Simulación de Error): {'PASADO ✅' if t2_ok else 'FALLIDO ❌'}")
    
    if t1_ok and t2_ok:
        print("\n🎉 TODAS LAS PRUEBAS COMPLETADAS CON ÉXITO")
        sys.exit(0)
    else:
        print("\n⚠️ ALGUNAS PRUEBAS FALLARON")
        sys.exit(1)

if __name__ == "__main__":
    main()
