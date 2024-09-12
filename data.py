import serial
import time
import threading
import matplotlib.pyplot as plt

# Configura a porta serial (substitua 'COM5' pela porta correta)
arduino = serial.Serial('COM5', 115200, timeout=1)

time.sleep(2)  # Aguarda o Arduino reiniciar

rpm_valores = []
capturando_dados = False
captura_terminada = False
marca_velocidade = None  # Variável para armazenar o índice de mudança de velocidade

def limpar_buffer_serial():
    """Limpa o buffer da porta serial."""
    arduino.flushInput()
    arduino.flushOutput()

def capturar_rpm_por_60_segundos():
    """Captura os valores de RPM por 60 segundos e os armazena em uma lista."""
    global capturando_dados, captura_terminada, marca_velocidade
    capturando_dados = True
    rpm_valores.clear()  # Limpa os valores anteriores
    
    start_time = time.time()  # Inicia o tempo de captura
    marca_velocidade = None  # Reseta a marca de velocidade

    while time.time() - start_time < 60:  # Coleta por 60 segundos
        if arduino.in_waiting > 0:
            linha = arduino.readline().decode('utf-8').strip()
            if linha.isdigit():  # Verifica se o valor recebido é um número
                rpm = int(linha)
                rpm_valores.append(rpm)
                print(f"RPM capturado: {rpm}")
        
        # Após 30 segundos, envia o valor "60" para aumentar a velocidade
        if time.time() - start_time >= 30 and marca_velocidade is None:
            enviar_velocidade("60")
            marca_velocidade = len(rpm_valores)  # Marca o ponto no gráfico
            print("Velocidade '60' enviada ao Arduino após 30 segundos.")

    capturando_dados = False
    captura_terminada = True
    print("Captura de RPM finalizada.")

def enviar_velocidade(velocidade):
    """Envia um valor de velocidade para o Arduino."""
    comando = "2\n"+velocidade + '\n'
    arduino.write(comando.encode())  # Envia o comando
    time.sleep(1)  # Aguarda o Arduino processar
    resposta = arduino.readline().decode('utf-8').strip()  # Lê a resposta
    if resposta:
        print(f"Resposta do Arduino: {resposta}")

def enviar_comando():
    """Permite ao usuário enviar comandos enquanto captura dados."""
    while True:
        comando = input("Digite o comando para o Arduino (ou 'exit' para sair): ")
        if comando == 'exit':
            break
        arduino.write((comando + '\n').encode())  # Envia o comando
        time.sleep(1)  # Dá tempo para o Arduino processar e responder
        resposta = arduino.readline().decode('utf-8').strip()  # Lê a resposta
        if resposta:
            print(f"Resposta do Arduino: {resposta}")
        
        # Inicia a captura de RPM por 60 segundos se o comando for '3'
        if comando == '3' and not capturando_dados:  # Verifica se a captura já está acontecendo
            limpar_buffer_serial()  # Limpa o buffer da serial antes de iniciar a captura
            print("Iniciando captura de RPM por 60 segundos...")
            captura_thread = threading.Thread(target=capturar_rpm_por_60_segundos)
            captura_thread.start()

def plotar_grafico():
    """Plota um gráfico dos valores de RPM e insere marcas e médias no gráfico."""
    if rpm_valores:  # Verifica se há valores a serem plotados
        if marca_velocidade is not None:
            rpm_antes_marca = rpm_valores[:marca_velocidade]
            rpm_depois_marca = rpm_valores[marca_velocidade:]

            media_antes_marca = sum(rpm_antes_marca) / len(rpm_antes_marca) if rpm_antes_marca else 0
            media_depois_marca = sum(rpm_depois_marca) / len(rpm_depois_marca) if rpm_depois_marca else 0

            print(f"Média de RPM antes da mudança de velocidade: {media_antes_marca:.2f}")
            print(f"Média de RPM após a mudança de velocidade: {media_depois_marca:.2f}")

        plt.figure(figsize=(10, 5))
        plt.plot(rpm_valores, marker='o', linestyle='-', color='b', label='RPM')

        # Adiciona a linha da média antes da mudança de velocidade
        if marca_velocidade is not None:
            plt.axhline(y=media_antes_marca, color='r', linestyle='--', label=f'Média Antes: {media_antes_marca:.2f}')
            plt.axhline(y=media_depois_marca, color='orange', linestyle='--', label=f'Média Depois: {media_depois_marca:.2f}')
            plt.axvline(x=marca_velocidade, color='g', linestyle='--', label='Mudança de Velocidade')

        # Define o título e os rótulos dos eixos
        plt.title('Valores de RPM Capturados')
        plt.xlabel('Amostras')
        plt.ylabel('RPM')

        # Define os limites e intervalos dos eixos
        plt.yticks(range(0, 5001, 500))  # Eixo y de 0 a 5000, com passos de 500
        plt.grid(True)

        plt.legend()  # Exibe a legenda
        plt.show()
    else:
        print("Nenhum valor de RPM foi capturado para plotar.")

def monitorar_captura():
    """Monitora a captura e plota o gráfico quando a captura terminar."""
    global captura_terminada
    while True:
        if captura_terminada:
            plotar_grafico()
            captura_terminada = False  # Reseta para a próxima captura
            break

try:
    # Inicia a thread para enviar comandos e permitir ajustes de velocidade
    comando_thread = threading.Thread(target=enviar_comando)
    comando_thread.start()

    # Monitora a captura de dados e plota o gráfico ao terminar
    monitorar_captura()

except KeyboardInterrupt:
    print("Programa interrompido.")

finally:
    arduino.close()  # Fecha a porta serial
