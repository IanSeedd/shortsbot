# src/hardware_detector.py
import psutil
import subprocess
import platform
import os
import warnings

def tem_placa_nvidia():
    """Verifica se há placa NVIDIA disponível para CUDA."""
    try:
        # Para Windows
        if platform.system() == "Windows":
            result = subprocess.run(['nvidia-smi', '--list-gpus'], capture_output=True, text=True)
            if result.returncode == 0 and result.stdout.strip():
                return True
        # Para Linux
        elif platform.system() == "Linux":
            result = subprocess.run(['nvidia-smi'], capture_output=True, text=True)
            if result.returncode == 0:
                return True
        # Para macOS (não suporta CUDA, mas pode ter GPU)
        else:
            # No macOS, podemos verificar se há GPU da Apple, mas não suporta CUDA
            pass
    except FileNotFoundError:
        pass
    return False

def detectar_config_otimizada():
    """
    Detecta a configuração do hardware e retorna um dicionário com configurações otimizadas
    para manter a qualidade (large-v3 + IA) mas minimizar o impacto no sistema.
    """
    print("Detectando hardware para otimização...")
    
    # Informações básicas
    ram_total_gb = psutil.virtual_memory().total / (1024**3)
    ram_disponivel_gb = psutil.virtual_memory().available / (1024**3)
    cpu_cores = psutil.cpu_count(logical=False) or psutil.cpu_count(logical=True)
    cpu_threads = os.cpu_count() or 4
    cpu_uso = psutil.cpu_percent(interval=1)

    threads_recomendadas = max(
        2,
        int(
            cpu_threads *
            ((100 - cpu_uso) / 100) *
            0.80
        )
    )
    
    # Verificar GPU NVIDIA
    nvidia_disponivel = tem_placa_nvidia()
    
    print(f"   • CPU Cores: {cpu_cores}")
    print(f"   • CPU Threads: {cpu_threads}")
    print(f"   • RAM Total: {ram_total_gb:.1f} GB")
    print(f"   • RAM Disponível: {ram_disponivel_gb:.1f} GB")
    print(f"   • NVIDIA GPU: {'Sim' if nvidia_disponivel else 'Não'}")
    
    # Configurações base
    config = {
        'modelo_mapeamento': 'base',          # Para mapeamento inicial (clip_selector)
        'threads_ffmpeg': threads_recomendadas, # Limita a CPU
        'modelo_final': 'large-v3',           # Para clipes finais (obrigatório)
        'usar_groq': True,                    # IA obrigatória
        'usar_fp16': nvidia_disponivel,       # Usar fp16 apenas se tiver NVIDIA
        'limitar_memoria': ram_disponivel_gb < 6, 
        'max_paralelo': 1,                    # Número de clipes processados em paralelo
        'pausa_entre_clipes': 5,              # Pausa entre clipes em segundos
        'limitar_segmentos': 50,              # Limite de segmentos por clipe para evitar sobrecarga
    }
    
    # Ajustes baseados na RAM e CPU
    if ram_total_gb >= 32 and cpu_cores >= 8:
        config['max_paralelo'] = 2
        config['pausa_entre_clipes'] = 3
        print("   PC Potente: Paralelismo ativado (2 clipes por vez)")
    elif ram_total_gb >= 16 and cpu_cores >= 6:
        config['max_paralelo'] = 1
        config['pausa_entre_clipes'] = 5
        print("   PC Intermediário: Processamento sequencial com pausas")
    else:
        config['max_paralelo'] = 1
        config['pausa_entre_clipes'] = 10
        config['limitar_segmentos'] = 30
        print("   PC Básico: Processamento lento com pausas longas")
    
    # Se a RAM disponível estiver baixa, aumentar pausas e reduzir paralelismo
    if ram_disponivel_gb < 4:
        config['max_paralelo'] = 1
        config['pausa_entre_clipes'] = 10
        print("   RAM baixa: Aumentando pausas e desativando paralelismo")
    
    # Se tiver NVIDIA, ativar fp16
    if nvidia_disponivel:
        print("   NVIDIA GPU detectada: Ativando fp16 para Whisper")
    
    return config

def monitorar_recursos():
    """Monitora o uso de recursos e sugere pausas se necessário."""
    ram_percent = psutil.virtual_memory().percent
    cpu_percent = psutil.cpu_percent(interval=1)
    
    print(f"   Monitor: CPU {cpu_percent}%, RAM {ram_percent}%")
    
    if ram_percent > 90:
        print("   RAM muito alta, considere aumentar pausas.")
        return True
    elif cpu_percent > 90:
        print("   CPU muito alta, considere aumentar pausas.")
        return True
    
    return False