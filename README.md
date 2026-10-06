# Controle nativo de painel LED via Bluetooth BLE

Projeto de engenharia reversa e controle de um painel LED iPixel através de Bluetooth Low Energy (BLE), utilizando Python e a biblioteca Bleak.

O objetivo é controlar o painel diretamente pelo Linux, sem depender do aplicativo oficial iPixel Color.

Atualmente já é possível enviar textos, controlar a cor RGB, gerar os glyphs utilizados pelo painel, calcular o CRC32 exigido pelo protocolo e selecionar diferentes modos de exibição.

---

## Status

**Funcionando**

| Recurso                            | Status             |
| ---------------------------------- | ------------------ |
| Conexão BLE                        | Funcionando        |
| Comunicação com FA02               | Funcionando        |
| Envio de texto                     | Funcionando        |
| Textos com múltiplos caracteres    | Funcionando        |
| Glyphs/fontes                      | Funcionando        |
| CRC32                              | Funcionando        |
| Cores RGB                          | Funcionando        |
| Texto estático                     | Funcionando        |
| Animações `01` a `08`              | Em investigação    |
| Textos maiores que a tela          | Em desenvolvimento |
| Interface web                      | Em desenvolvimento |
| Controle por usuários/autenticação | Futuro             |
| Integração com Google Calendar     | Futuro             |

---

## Objetivo

A ideia inicial era simplesmente conseguir enviar um texto para o painel sem utilizar o aplicativo oficial.

Durante o processo, o projeto evoluiu para a engenharia reversa do protocolo utilizado pelo iPixel Color.

O objetivo final é construir uma forma própria de controlar o painel, permitindo:

* Texto personalizado
* Cores RGB
* Animações
* Textos maiores que a área visível
* Controle através de uma interface web
* Possivelmente velocidade, brilho e outros parâmetros
* Integrações externas, como Google Calendar

---

## Hardware

Painel LED utilizado nos testes:

```text
Nome BLE: LED_BLE_AB37E254
Resolução: 64 x 20 pixels
```

O painel utiliza Bluetooth Low Energy para receber os comandos.

> O endereço MAC do painel não é publicado neste repositório.

---

## Comunicação BLE

Durante a engenharia reversa foram identificados os seguintes serviços e características.

### Serviço principal

```text
000000fa-0000-1000-8000-00805f9b34fb
```

### Característica de escrita

```text
FA02

0000fa02-0000-1000-8000-00805f9b34fb
```

Propriedades:

```text
Write
Write Without Response
```

### Característica de notificação

```text
FA03
```

Também foram identificadas:

```text
AE00
AE01 -> Write Without Response
AE02 -> Notify
```

A comunicação utilizada pelo projeto atualmente ocorre principalmente através da FA02.

---

## Uma comunicação por vez

O painel não aceita simultaneamente a conexão do aplicativo iPixel Color e a conexão feita pelo Python.

Portanto, durante os testes:

```text
iPixel Color conectado
        |
        X
Python conectado
```

Para utilizar o script, o aplicativo oficial deve estar desconectado do painel.

---

# Engenharia reversa

A descoberta do protocolo foi feita comparando o comportamento do aplicativo oficial com os dados realmente transmitidos pelo Bluetooth.

Foram utilizados:

* Android
* iPixel Color
* Bluetooth HCI Snooping
* Wireshark
* tshark
* ADB
* JADX
* Smali
* Capturas controladas de pacotes
* Python
* Bleak

Aplicativo analisado:

```text
Package: com.wifiled.ipixels
VersionName: 3.7.8
VersionCode: 380
```

Durante a análise do APK também foram encontradas classes relacionadas ao envio:

```text
SendCore.java
BleManager.java
BleManager2.java
GifCore.java
```

---

# Estrutura do protocolo

Uma operação de envio de texto utiliza uma sequência de cinco escritas no BLE:

```text
Write 1
Write 2
Write 3
Write 4
Write 5
```

O Write 5 é o principal pacote de dados e contém as informações necessárias para renderizar o texto.

Um ponto importante descoberto durante a investigação é que esses cinco writes pertencem à operação de envio como um todo.

Por exemplo, ao enviar:

```text
WEBHULK
```

o aplicativo não envia cinco writes para cada letra.

São cinco writes no total, sendo o quinto um pacote maior contendo os dados de todas as letras.

---

# Glyphs

O painel não recebe simplesmente caracteres ASCII.

Cada caractere é transformado em um bitmap de 10 bytes, que representa o desenho da letra.

Por exemplo:

```text
A = 1c 36 63 63 63 7f 63 63 63 63
```

Representação:

```text
    ███
   ██ ██
  ██   ██
  ██   ██
  ██   ██
  ████████
  ██   ██
  ██   ██
  ██   ██
  ██   ██
```

Outros glyphs já identificados incluem:

```text
O = 3e63636363636363633e
W = 6363636b6b6b7f776363
E = 7f6606263e260606667f
B = 3f6666663e666666663f
H = 636363637f6363636363
U = 6363636363636363633e
L = 0f06060606060646667f
K = 6333331b0f0f1b336363
```

Esses glyphs foram obtidos diretamente das capturas do aplicativo.

---

# Cores RGB

A cor do texto pode ser definida diretamente no pacote.

O protocolo aceita valores RGB de:

```text
R = 0-255
G = 0-255
B = 0-255
```

Por exemplo:

```python
rgb = (0, 255, 0)
```

envia o texto em verde.

Testes com diferentes combinações de RGB foram realizados com sucesso.

---

# CRC32

Uma das descobertas importantes foi a identificação do checksum utilizado pelo protocolo.

O painel utiliza CRC32 padrão, calculado através dos dados do payload.

Em Python:

```python
import struct
import zlib

crc = zlib.crc32(data) & 0xFFFFFFFF
crc_bytes = struct.pack("<I", crc)
```

O resultado precisa ser enviado em Little-Endian.

O cálculo foi validado comparando o resultado produzido pelo Python com os valores encontrados nas capturas do aplicativo.

Exemplo:

```text
CRC capturado:
c1 c7 97 5b

CRC calculado:
c1 c7 97 5b
```

O mesmo comportamento também foi confirmado em um pacote contendo a palavra:

```text
WEBHULK
```

com o CRC calculado sobre o payload completo.

---

# Animações

Uma das descobertas mais recentes do projeto foi a identificação do campo que seleciona o modo de exibição.

Dentro do pacote existe a sequência:

```text
00 01 01 XX 50 00
         |
       modo
```

O valor `XX` determina o modo de exibição.

A descoberta atual é:

| Valor | Modo       |
| ----- | ---------- |
| `00`  | Estático   |
| `01`  | Animação 1 |
| `02`  | Animação 2 |
| `03`  | Animação 3 |
| `04`  | Animação 4 |
| `05`  | Animação 5 |
| `06`  | Animação 6 |
| `07`  | Animação 7 |
| `08`  | Animação 8 |

Ou seja, o protocolo possui pelo menos 9 modos de exibição identificados, sendo um estático e oito animações.

O funcionamento visual individual das animações `01` até `08` ainda está sendo documentado.

A descoberta foi feita alterando somente esse campo e recalculando o CRC do pacote.

Por exemplo:

```text
00 01 01 00 50 00
```

corresponde ao modo estático.

Enquanto:

```text
00 01 01 01 50 00
```

ativa uma animação.

---

# Estrutura dos caracteres

O primeiro caractere possui uma estrutura diferente dos caracteres seguintes.

Primeiro caractere:

```python
def build_first_char(char, rgb):
    return (
        bytes(rgb)
        + bytes(5)
        + bytes(rgb)
        + bytes(3)
        + FONT_MAP[char]
        + bytes(3)
    )
```

Demais caracteres:

```python
def build_next_char(char, rgb):
    return (
        bytes(1)
        + bytes(rgb)
        + bytes(3)
        + FONT_MAP[char]
        + bytes(3)
    )
```

Essa estrutura foi validada comparando os pacotes gerados pelo projeto com as capturas do aplicativo oficial.

---

# Teste WEBHULK

Um dos testes utilizados para validar o protocolo foi o envio da palavra:

```text
WEBHULK
```

em verde:

```python
texto = "WEBHULK"
rgb = (0, 255, 0)
```

O painel recebeu corretamente:

```text
WEBHULK
```

O teste confirmou simultaneamente:

```text
Texto                    Funcionando
Glyphs                   Funcionando
RGB                      Funcionando
CRC32                    Funcionando
BLE                      Funcionando
Múltiplos caracteres     Funcionando
```

Também foi possível comparar o pacote completo capturado no Wireshark com o pacote gerado pelo Python.

---

# Projeto em Python

O controle atual utiliza:

```text
Python
    |
    +-- Bleak
          |
          +-- Bluetooth Low Energy
                    |
                    +-- Painel LED
```

A biblioteca principal utilizada é:

```text
bleak==3.0.2
```

As demais bibliotecas utilizadas pelo código atual fazem parte da biblioteca padrão do Python.

---

# Instalação

Clone o repositório:

```bash
git clone https://github.com/zanataa/led-ipixel.git
cd led-ipixel
```

Crie o ambiente virtual:

```bash
python3 -m venv venv
```

Ative:

```bash
source venv/bin/activate
```

Instale a dependência:

```bash
pip install -r requirements.txt
```

---

# Execução

O script principal atualmente utilizado no projeto é:

```text
enviartexto.py
```

Antes de executar:

1. Ligue o painel.
2. Certifique-se de que ele está disponível via Bluetooth.
3. Feche ou desconecte o iPixel Color.
4. Ative o ambiente virtual.
5. Execute o script.

Exemplo:

```bash
source venv/bin/activate
python3 enviartexto.py
```

A implementação atual está focada no protocolo nativo descoberto durante a engenharia reversa.

---

# Estrutura do projeto

Atualmente o repositório mantém somente os arquivos necessários para a implementação funcional:

```text
led-ipixel/
├── enviartexto.py
├── requirements.txt
├── .gitignore
└── README.md
```

Os arquivos utilizados durante a investigação, como capturas HCI, dumps, APKs, arquivos decompilados e scripts experimentais, não fazem parte da implementação principal.

---

# Como o protocolo foi descoberto

O processo basicamente foi:

```text
iPixel Color
      |
Bluetooth HCI Snooping
      |
Captura dos pacotes
      |
Wireshark / tshark
      |
Comparação entre caracteres
      |
Identificação dos glyphs
      |
Identificação do CRC32
      |
Montagem dos pacotes em Python
      |
Teste direto no painel
      |
Validação
```

A engenharia reversa foi feita de forma incremental, alterando uma variável por vez e comparando o comportamento do painel.

---

# Próximos passos

Alguns dos próximos objetivos do projeto são:

* [ ] Identificar visualmente todas as animações `01` a `08`
* [ ] Implementar seleção de animação no Python
* [ ] Melhorar suporte a textos maiores que a largura do painel
* [ ] Investigar velocidade das animações
* [ ] Investigar brilho
* [ ] Ampliar o mapa de glyphs
* [ ] Integrar o protocolo nativo à interface web
* [ ] Criar controle por usuários
* [ ] Adicionar autenticação
* [ ] Estudar integração com Google Calendar

---

# Sobre este projeto

Este projeto nasceu como um experimento para entender como um painel LED aparentemente simples se comunica através de Bluetooth.

O objetivo não foi apenas fazer o painel funcionar, mas entender como os dados são construídos e transmitidos, reproduzindo o protocolo utilizado pelo aplicativo oficial em Python.

Cada parte do protocolo apresentada neste README foi descoberta através de captura, comparação, implementação e testes no hardware real.

---

# Aviso

Este projeto é destinado a fins de estudo, pesquisa e interoperabilidade com hardware próprio.

O protocolo documentado aqui foi obtido através de engenharia reversa e testes experimentais. Algumas partes ainda estão em investigação e podem mudar conforme novas descobertas forem feitas.
