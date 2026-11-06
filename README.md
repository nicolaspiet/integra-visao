# Integra Visão

Cinco experiências com webcam para o Integra Profissões, com menu, jogos e catálogo em uma única janela em português. Aplicação Python com execução local e aceleração opcional por GPU.

## Instalação em outro computador

Requer Git, Python **3.12**, webcam e acesso à internet na preparação. Linux foi validado em CachyOS com RTX 4060 Laptop; Windows e macOS ainda não foram validados. GPU é opcional: comece com `--device cpu` para maior compatibilidade. O modo GPU depende do suporte OpenGL ES/EGL do MediaPipe e dos drivers da máquina; ter CUDA instalado não basta.

```bash
git clone https://github.com/nicolaspiet/integra-visao.git
cd integra-visao
```

### Linux (ou macOS com dependências compatíveis)

Instale [uv](https://docs.astral.sh/uv/getting-started/installation/) e execute:

```bash
./preparar.sh
./iniciar.sh
```

Depois da preparação, `iniciar.sh` abre o menu com as configurações padrão. Use `jogar.sh` quando quiser passar flags diretamente.

O script cria `.venv` com Python 3.12, instala `requirements.lock`, baixa os arquivos dos projetos originais e gera o guia offline. Não modifica o Python do sistema. Em Linux, `v4l2-ctl` (pacote `v4l-utils`) é opcional para ajustar temporariamente o FPS da webcam. O programa tenta V4L2 e backend genérico, além de YUYV e MJPG; isso ajuda com DroidCam. Se houver mais de uma câmera, use `--camera 1` (ou outro índice). Bibliotecas gráficas OpenGL/EGL e uma sessão gráfica são necessárias para a janela.

### Windows (PowerShell)

Com Python 3.12 e Git instalados:

```powershell
py -3.12 -m venv .venv
.\.venv\Scripts\python.exe -m pip install -r requirements.lock
.\.venv\Scripts\python.exe tools/prepare_assets.py
.\.venv\Scripts\python.exe tools/build_guide.py
.\.venv\Scripts\python.exe main.py --device cpu
```

Depois da instalação, também é possível dar duplo clique em `iniciar.bat`.

Não é necessário ativar o ambiente. Nos exemplos seguintes, substitua `./jogar.sh` por `.\.venv\Scripts\python.exe main.py` no Windows. Se não existir um pacote compatível com seu sistema/arquitetura, a instalação falhará; não há garantia de suporte para todas as plataformas.

A preparação baixa código e imagens do Expression Lab e alinhamento/modelo do OpenCV Zoo diretamente de revisões fixadas dos autores. Esses arquivos não são redistribuídos neste repositório. Consulte os termos das fontes abaixo antes de redistribuí-los. Após a preparação, a execução funciona offline.

O programa inicia em tela cheia. **F11** alterna entre tela cheia e janela; `./jogar.sh --windowed` inicia em janela. Escolha um jogo com o mouse ou com as teclas `1` a `5`. A câmera só liga ao entrar em um modo e é liberada ao voltar ao início.

1. **Pong com a mão:** o indicador controla a raquete da esquerda; o computador controla a da direita. Partida de 45 segundos e recorde local.
2. **Desafio das expressões:** imite a expressão pedida. O modelo estima alegria, tristeza, raiva, medo, surpresa, nojo e expressão neutra. Mantenha a estimativa por aproximadamente 0,7 segundo para pontuar. `N` pula um alvo difícil; o alvo também muda após nove segundos de resultados válidos.
3. **Corte as frutas:** corte com o indicador, evite bombas e some pontos em 45 segundos.
4. **Figurinhas / Expression Lab:** gestos e expressões acionam os memes do projeto de CaioScura. A integração usa os módulos originais e modelos locais em uma nova interface, com captura independente e detectores acelerados.
5. **Anatomia da visão:** mostra os 478 landmarks do rosto, os 21 landmarks de cada mão, conexões, contornos, índices e blendshapes faciais.
6. **Teste da webcam:** mostra captura, rastreamento, tempos e dispositivo utilizado.

`ESPAÇO`: começar/repetir ou pausar; `P`: pausar; `F11` ou `F`: alternar tela cheia; `ESC` ou `Q`: voltar ao início (no início, encerra). Fechar a janela ou clicar em **Sair** encerra o programa. O tempo dos jogos para quando mão ou rosto saem do enquadramento.

## Câmera maior e catálogo

A interface usa fundo claro, linhas simples e controles discretos. Nos modos de rosto, a câmera ocupa a área principal. Nos jogos de mão, `C` ou **Câmera maior** troca a prioridade entre câmera e jogo, sem modificar a resolução de captura. A proporção do vídeo é preservada. FPS, backend e linhas das mãos ficam ocultos por padrão; `D` os mostra durante o jogo.

**Como jogar** ou `H` abre o catálogo na própria janela e suspende a atualização da partida. São **15 figurinhas**, com as imagens originais e instruções de cada gesto, e **7 expressões**, com esquemas ilustrativos e dicas. Clique em um item para abrir os detalhes; setas e rolagem navegam entre páginas ou itens. **Voltar** ou `H` retorna ao jogo. `N` ou **Pular esta** troca a expressão pedida no desafio.

No modo **Anatomia**, as teclas `1` a `6` ligam ou desligam, respectivamente: mãos e ossos, rosto, malha facial, contornos, índices e blendshapes. Os mesmos controles aparecem no painel lateral. Índices começam desligados para manter a imagem limpa; ative-os quando quiser inspecionar cada landmark.

A câmera começa espelhada, como no celular. O botão **Desespelhar** (tecla `M`) troca essa visualização. **Preencher câmera** (tecla `V`) estica o quadro para ocupar todo o painel; **Tamanho real** volta a preservar a proporção. Esses controles mudam somente a prévia, não a resolução nem o detector.

No modo Figurinhas, o reconhecimento agora tolera mais variação de ângulo, distância e pequenas perdas de um quadro. O resultado permanece por uma fração de segundo antes de desaparecer, reduzindo a piscada causada pelo DroidCam ou por mãos parcialmente oclusas.

Para mostrar os mesmos pontos e conexões por cima dos minigames, ative o modo opcional `--debug-overlay` (ou o alias `--show-skeleton`). Ele deixa a partida normal quando omitido:

```bash
./jogar.sh --game expressions --debug-overlay
./jogar.sh --game pong --show-skeleton
```

Os esquemas faciais são dicas de atuação, não imagens do conjunto de treino nem garantia de classificação. Medo e nojo podem ser confundidos pelo modelo. As regras das figurinhas têm prioridades e podem se sobrepor; por exemplo, apontar para cima difere de apontar para o lado, e o gesto de nojo usa o nariz franzido, não a língua.

Um guia completo, offline e independente da webcam está em [docs/referencias.html](docs/referencias.html). Inclui referências de todos os jogos. Para regenerá-lo após alterar o catálogo: `.venv/bin/python tools/build_guide.py` (não abre janela, navegador ou câmera).

## Todas as flags

As opções podem ser combinadas. `./jogar.sh --help` mostra a ajuda atual.

| Flag | Valores / padrão | Efeito |
|---|---|---|
| `-h`, `--help` | — | Mostra ajuda e encerra sem abrir a câmera. |
| `--game` | `pong`, `expressions`, `fruit`, `memes`, `camera`, `anatomy`; padrão: menu | Abre diretamente um modo. |
| `--device` | `auto` (padrão), `cpu`, `gpu` | `auto` tenta GPU e permite CPU; `cpu` força CPU; `gpu` exige GPU e falha se indisponível. |
| `--camera` | inteiro; padrão `0` | Índice do dispositivo de vídeo. |
| `--width` | `640` (padrão), `1280` | Largura solicitada à câmera. |
| `--height` | `360`, `480` (padrão), `720` | Altura solicitada à câmera; depende do suporte do dispositivo. |
| `--fps` | `30`, `60` (padrão), `120` | Limite da interface, não da captura física. |
| `--duration` | segundos; padrão `45` | Duração das partidas com pontuação. |
| `--dynamic-fps` | desligada por padrão | Preserva o controle de FPS dinâmico da webcam no Linux. |
| `--demo` | desligada por padrão | Demonstração automática sem webcam e sem salvar recordes. |
| `--fullscreen` | ligado por padrão | Inicia em tela cheia. |
| `--no-fullscreen`, `--windowed` | — | Inicia em janela; F11 alterna depois. |
| `--seconds` | segundos; padrão `0` | Encerra a janela automaticamente; `0` não impõe limite. |
| `--screenshot` | caminho de arquivo | Salva imagem da janela ao sair. |
| `--benchmark` | segundos | Mede captura/inferência reais sem janela; **usa webcam**. |
| `--debug-overlay`, `--show-skeleton` | desligadas por padrão | Sobrepõe pontos das mãos e malha do rosto nos minigames. |

Exemplos:

```bash
./jogar.sh --device cpu --windowed
./jogar.sh --game expressions --device gpu --debug-overlay
./jogar.sh --game fruit --device cpu --duration 60 --fps 30
./jogar.sh --game camera --camera 0 --width 1280 --height 720
./jogar.sh --game pong --demo --seconds 10
```

## GPU, captura e desempenho

O programa tenta usar o delegate GPU do MediaPipe. Neste notebook, GLVND é direcionado à NVIDIA antes de carregar os modelos. **A aceleração é OpenGL ES, não CUDA.** O detector facial e o de mãos usam GPU; o classificador pequeno de expressões usa OpenCV DNN na CPU. Os blendshapes usados no modo de memes também podem usar CPU internamente.

Pressione `D` durante um jogo para ver o backend e as métricas no rodapé. `--device gpu` exige inicialização na GPU e mostra erro se falhar. `--device auto` permite CPU com aviso; `--device cpu` permite comparar. Detalhes do renderizador ficam em `logs/runtime.log`.

```bash
./jogar.sh --game pong --device gpu
./jogar.sh --game expressions --device gpu
./jogar.sh --game pong --device cpu --benchmark 8
./jogar.sh --game pong --device gpu --benchmark 8
./jogar.sh --game camera --width 1280 --height 720
```

Captura e inferência usam threads independentes em um processo separado da interface. Isso isola o contexto EGL da NVIDIA do contexto gráfico SDL, que apresentou conflito neste notebook. Um único quadro recente é mantido, sem fila crescente. Apenas a prévia reduzida e os resultados cruzam processos. A interface tem limite de aproximadamente 60 FPS; isso não muda a frequência física da webcam. Os jogos usam tempo transcorrido, suavização independente de FPS e colisão por subpassos/segmentos para movimentos rápidos. Só os detectores necessários a cada modo são carregados. Prévia e textos são reutilizados quando possível.

640×480 usa YUYV por padrão; 1280×720 usa MJPEG porque a câmera integrada anuncia 30 FPS nesse formato e apenas 10 FPS em YUYV a 720p. O número anunciado não garante a frequência real em baixa iluminação: o rodapé mede o recebimento de quadros.

Enquanto a câmera está aberta, o programa tenta desativar `exposure_dynamic_framerate`, restaurando seu valor anterior ao sair normalmente. `--dynamic-fps` preserva esse controle. Nenhum ajuste de brilho, exposição, balanço de branco ou configuração global do sistema é persistido. Ilumine rosto e mãos pela frente; filtros pesados e super-resolução não são usados.

`Inferência` mede o processamento de um quadro; `Quadro` mostra a idade desde seu recebimento pelo programa. **Esses números não incluem exposição do sensor nem latência física do monitor.** Benchmarks sem mãos/rostos detectados medem principalmente o caminho de detecção, não garantem desempenho durante uma partida.

## Diagnóstico e testes

```bash
.venv/bin/python -m unittest discover -s tests -v
./jogar.sh --game pong --demo --seconds 5
./jogar.sh --game fruit --demo --seconds 5
```

Os testes unitários e de interface desenham em superfícies de memória; não abrem janela nem webcam. Cobrem menu, cliques, F11, retorno ao início, catálogo completo, pausa e regras dos jogos. Para forçar execução sem vídeo: `SDL_VIDEODRIVER=dummy SDL_AUDIODRIVER=dummy .venv/bin/python -m unittest discover -s tests -v`.

Os comandos `./jogar.sh ... --demo` acima abrem a janela para uma demonstração manual, sem acessar webcam nem gravar recordes. `--seconds` fecha automaticamente. `--screenshot caminho.png` salva uma imagem da janela somente quando solicitado. Em operação normal não são gravadas fotos ou vídeos; apenas recordes em `data/records.json` e logs técnicos em `logs/runtime.log`.

Se a câmera não abrir, feche outros aplicativos que a utilizam ou tente `--camera 1` (somente se esse dispositivo oferecer captura de vídeo). Confira `logs/runtime.log` se GPU ou interface falharem. Não é necessário executar como root.

Para reconstruir o ambiente, execute `./preparar.sh`. Isso exige internet e `uv`; dependências completas estão fixadas em `requirements.lock`.

## Origem e licenças

- [Expression Lab — CaioScura](https://github.com/CaioScura/expression-lab): checkout local original em `vendor/expression-lab`, commit `0602ac047eebc959c44caa8c769b2bd4f1a13ea5`. Seus arquivos não foram alterados. O repositório consultado não apresenta licença explícita; não se deve atribuir a ele uma licença inventada ou assumir permissão ampla de redistribuição. Memes mantêm os direitos de seus respectivos autores.
- [OpenCV Zoo — Progressive Teacher / MobileFaceNet](https://github.com/opencv/opencv_zoo/tree/main/models/facial_expression_recognition): classificador de sete expressões, código de alinhamento original e modelo ONNX. Licença Apache 2.0 preservada em `vendor/opencv-zoo/LICENSE`; modelo baixado do armazenamento oficial do projeto.
- [MediaPipe Hand Landmarker](https://ai.google.dev/edge/mediapipe/solutions/vision/hand_landmarker/python): rastreamento temporal em modo VIDEO evita repetir detecção completa em todo quadro.
- [V4L2](https://docs.kernel.org/userspace-api/media/v4l/ext-ctrls-camera.html): controles da câmera no Linux.

As estimativas de expressão são uma brincadeira baseada na aparência do rosto; não confirmam sentimentos. A precisão depende de luz, ângulo e pessoa. FPS, classificação e experiência precisam ser conferidos com participantes no local da feira.
