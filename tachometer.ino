// Definições de pinos e variáveis
const int IR_PIN = 2;  // Pino do sensor IR
const int motorPin = 3;  // Pino do motor

volatile unsigned int counter = 0;  // Variável do contador para revoluções
unsigned long previousMillis = 0;  // Armazena o tempo anterior
unsigned int rpm = 0;  // Variável para armazenar o valor de RPM
bool countRPM = false;  // Flag para controle de contagem de RPM

// Função de interrupção do sensor IR
void IRinterrupt() {
  if (countRPM) {
    counter++;
  }
}

void setup() {
  // Configurações do sensor IR e motor
  pinMode(IR_PIN, INPUT_PULLUP);
  attachInterrupt(digitalPinToInterrupt(IR_PIN), IRinterrupt, CHANGE);
  pinMode(motorPin, OUTPUT);
  
  // Inicializa a comunicação serial
  Serial.begin(115200);
  delay(2000);

  }

void loop() {
  // Controle do motor via Serial
  if (Serial.available()) {
    String input = Serial.readStringUntil('\n');
    input.trim();  // Remove espaços em branco ou novas linhas extras

    if (input.length() == 1) {
      char option = input.charAt(0);

      switch (option) {
        case '1':
          countRPM = true;  // Inicia a contagem de RPM
          handleSpeedLoop();
          stopMotor();
          countRPM = false;  // Para a contagem de RPM após o loop
          break;

        case '2':
          while (!Serial.available()) {}
          float speed = Serial.readStringUntil('\n').toFloat();
          countRPM = true;  // Inicia a contagem de RPM
          handleMotorControl(speed);
          break;

        default:
          Serial.println("Opção inválida. Por favor, selecione uma opção válida.");
          break;
      }
    } else {
      Serial.println("Por favor, insira um dígito correspondente a uma opção do menu.");
    }
  }

  // Calcula o RPM apenas quando a flag countRPM estiver ativa
  if (countRPM) {
    unsigned long currentMillis = millis();
    if (currentMillis - previousMillis >= 500) {
      detachInterrupt(digitalPinToInterrupt(IR_PIN));
      rpm = (counter / 6) * 60;  // Calcula o RPM
      counter = 0;
      attachInterrupt(digitalPinToInterrupt(IR_PIN), IRinterrupt, FALLING);
      previousMillis = currentMillis;
      // Envia apenas o valor de RPM
      Serial.println(rpm);
    }
  }
}

// Funções de controle do motor
void handleMotorControl(float speed) {  
  int pwmValue = map(speed, 0, 100, 96, 255);
  analogWrite(motorPin, pwmValue);
}

void handleSpeedLoop() {
  Serial.println("Iniciando loop de velocidade...");
  for (int speed = 0; speed <= 100; speed += 3) {
    handleMotorControl(speed);
    delay(100);
  }
  for (int speed = 100; speed >= 0; speed -= 3) {
    handleMotorControl(speed);
    delay(100);
  }
  Serial.println("Loop de velocidade concluído.");
}

void stopMotor() {
  analogWrite(motorPin, 0);
  Serial.println("Motor parado.");
}
