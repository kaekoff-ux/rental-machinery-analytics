/* LocaMaq · comportamento do site (Camada 1).
   Para personalizar, mude só os dois blocos de configuração logo abaixo. */

// ---------- Configuração 1: contatos ----------
// Telefones, e-mail e endereços aparecem em vários pontos da página; mude aqui e todos se atualizam.
// Escreva os telefones como devem aparecer na tela, com DDD; o link de ligação é montado sozinho.
// WhatsApp vazio ("") esconde o botão de WhatsApp. Exemplo: "(15) 90000-0000".
// Telegram: nome de usuário do chat bot, sem @ (ex.: "LocaMaqAtendimentoBot"). Vazio, o botão
// "Atendimento" abre um aviso de que o bot ainda vai entrar no ar (Camada 3 do projeto).
const CONTATO = {
  telefone: "(15) 0000-0000",
  whatsapp: "",
  telegram: "",
  email: "contato@locamaq.example",
  horario: "Segunda a sexta, das 7h às 18h. Sábado, das 7h às 12h.",
  unidades: {
    sorocaba: { endereco: "Av. Exemplo, 1000 · Sorocaba/SP", telefone: "(15) 0000-0000" },
    sao_paulo: { endereco: "Rua Exemplo, 200 · São Paulo/SP", telefone: "(11) 0000-0000" },
    campinas: { endereco: "Rua Exemplo, 300 · Campinas/SP", telefone: "(19) 0000-0000" },
    ribeirao_preto: { endereco: "Rua Exemplo, 400 · Ribeirão Preto/SP", telefone: "(16) 0000-0000" },
    sao_jose_dos_campos: { endereco: "Rua Exemplo, 500 · São José dos Campos/SP", telefone: "(12) 0000-0000" },
  },
};

// ---------- Configuração 2: destino do formulário (passo 5 do plano) ----------
// Cole aqui a URL do Web App do Google Apps Script (termina em /exec).
// Vazia, o formulário fica em modo local: confirma na tela e imprime os dados no console (F12).
const URL_APPS_SCRIPT = "";

const MENSAGEM_WHATSAPP = "Olá! Vim pelo site da LocaMaq e quero um orçamento.";
const INTERVALO_PREVENTIVA_HORAS = 250; // mesma regra de src/gerador_dados/gerar_ordens_manutencao.py
const movimentoReduzido = window.matchMedia("(prefers-reduced-motion: reduce)").matches;
const numeroBR = new Intl.NumberFormat("pt-BR");

const SETA_ESQUERDA = '<svg aria-hidden="true" width="18" height="18" viewBox="0 0 24 24"><path d="M15 5l-7 7 7 7" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"/></svg>';
const SETA_DIREITA = '<svg aria-hidden="true" width="18" height="18" viewBox="0 0 24 24"><path d="M9 5l7 7-7 7" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"/></svg>';

// ---------- Contatos na página ----------

function buscarContato(caminho) {
  return caminho.split(".").reduce((objeto, chave) => (objeto ? objeto[chave] : undefined), CONTATO);
}

function numeroInternacional(texto) {
  const digitos = texto.replace(/\D/g, "");
  return digitos.startsWith("55") && digitos.length > 11 ? digitos : "55" + digitos;
}

function preencherContatos() {
  document.querySelectorAll("[data-contato]").forEach((elemento) => {
    const caminho = elemento.dataset.contato;
    const valor = buscarContato(caminho);
    if (!valor) return;
    if (!elemento.hasAttribute("data-manter-texto")) elemento.textContent = valor;

    const link = elemento.closest("a");
    if (!link) return;
    if (caminho.endsWith("telefone")) link.href = "tel:+" + numeroInternacional(valor);
    if (caminho === "email") link.href = "mailto:" + valor;
    if (caminho === "whatsapp") {
      link.href = `https://wa.me/${numeroInternacional(valor)}?text=${encodeURIComponent(MENSAGEM_WHATSAPP)}`;
    }
  });

  document.querySelectorAll('[data-so-com="whatsapp"]').forEach((elemento) => {
    elemento.hidden = !CONTATO.whatsapp;
  });

  // Telegram: com o bot preenchido, abre o chat; sem ele, abre o pop-up de aviso.
  document.querySelectorAll("[data-telegram]").forEach((link) => {
    if (CONTATO.telegram) {
      link.href = `https://t.me/${CONTATO.telegram.replace(/^@/, "")}`;
      link.target = "_blank";
      link.rel = "noopener";
    } else {
      link.dataset.abrir = "modal-telegram";
    }
  });

  document.querySelectorAll("[data-ano]").forEach((elemento) => {
    elemento.textContent = new Date().getFullYear();
  });
}

// ---------- Carrossel de slides ----------

function iniciarCarrossel(raiz) {
  const trilho = raiz.querySelector(".slides");
  const slides = [...trilho.children];
  const comRotulos = raiz.hasAttribute("data-rotulos");

  slides.forEach((slide, i) => {
    slide.setAttribute("role", "group");
    slide.setAttribute("aria-roledescription", "slide");
    slide.setAttribute("aria-label", slide.dataset.rotulo || `${i + 1} de ${slides.length}`);
  });

  const controles = document.createElement("div");
  controles.className = "carrossel-controles";
  controles.innerHTML = `
    <button class="seta" type="button" aria-label="Anterior">${SETA_ESQUERDA}</button>
    <div class="carrossel-meio"><div class="carrossel-pontos"></div><span class="carrossel-contagem" aria-hidden="true"></span></div>
    <button class="seta" type="button" aria-label="Próximo">${SETA_DIREITA}</button>`;
  const [anterior, proximo] = controles.querySelectorAll(".seta");
  trilho.after(controles);

  const indicadores = slides.map((slide, i) => {
    const botao = document.createElement("button");
    botao.type = "button";
    botao.className = comRotulos ? "carrossel-rotulo" : "carrossel-ponto";
    if (comRotulos) botao.textContent = slide.dataset.rotulo;
    else botao.setAttribute("aria-label", `Ir para o slide ${i + 1}`);
    botao.addEventListener("click", () => irPara(i));
    return botao;
  });
  if (comRotulos) {
    const faixa = document.createElement("div");
    faixa.className = "carrossel-rotulos";
    faixa.append(...indicadores);
    trilho.before(faixa);
  } else {
    controles.querySelector(".carrossel-pontos").append(...indicadores);
  }

  const passo = () => (slides.length > 1 ? slides[1].offsetLeft - slides[0].offsetLeft : trilho.clientWidth);
  const porVez = () => Math.max(1, Math.round((trilho.clientWidth + 1) / passo()));
  const ultimo = () => Math.max(0, slides.length - porVez());
  const atual = () => Math.min(ultimo(), Math.round(trilho.scrollLeft / passo()));

  function irPara(indice, instantaneo = false) {
    const alvo = Math.max(0, Math.min(indice, ultimo()));
    trilho.scrollTo({ left: alvo * passo(), behavior: instantaneo || movimentoReduzido ? "auto" : "smooth" });
  }

  function atualizar() {
    if (!trilho.clientWidth) return;
    const i = atual();
    const fim = ultimo();
    indicadores.forEach((indicador, j) => {
      indicador.setAttribute("aria-current", String(j === i));
      indicador.hidden = !comRotulos && j > fim;
    });
    if (comRotulos) indicadores[i].scrollIntoView({ block: "nearest", inline: "nearest" });
    anterior.disabled = i <= 0;
    proximo.disabled = i >= fim;
    controles.querySelector(".carrossel-contagem").textContent = `${i + 1} / ${fim + 1}`;
    // Rolagem lateral só quando precisa: sem slides escondidos, os controles somem.
    controles.hidden = fim === 0;
  }

  anterior.addEventListener("click", () => irPara(atual() - 1));
  proximo.addEventListener("click", () => irPara(atual() + 1));
  trilho.addEventListener("scroll", () => requestAnimationFrame(atualizar), { passive: true });
  trilho.addEventListener("keydown", (evento) => {
    if (evento.target !== trilho) return;
    if (evento.key === "ArrowRight") { evento.preventDefault(); irPara(atual() + 1); }
    if (evento.key === "ArrowLeft") { evento.preventDefault(); irPara(atual() - 1); }
  });
  window.addEventListener("resize", atualizar);

  raiz.carrossel = { irPara, atualizar };
}

// ---------- Pop-ups ----------
// Qualquer botão ou link com data-abrir="id-do-pop-up" abre o pop-up; os outros data-* do botão
// (data-equipamento, data-observacao) chegam ao "preparador" daquele pop-up.

const preparadores = {};

function abrirModal(id, dados = {}) {
  const modal = document.getElementById(id);
  if (!modal || typeof modal.showModal !== "function") return false;
  document.querySelectorAll("dialog.modal[open]").forEach((aberto) => aberto.close());
  const focarDepois = preparadores[id] ? preparadores[id](dados) : null;
  modal.showModal();
  // Sem campo para focar, o foco vai para o próprio pop-up (sem anel no botão de fechar).
  if (!focarDepois) modal.focus();

  // Depois de visível, cada carrossel volta ao primeiro slide e recalcula os controles.
  modal.querySelectorAll("[data-carrossel]").forEach((raiz) => {
    raiz.carrossel.irPara(0, true);
    raiz.carrossel.atualizar();
  });
  if (focarDepois) focarDepois.focus();
  return true;
}

function iniciarModais() {
  document.addEventListener("click", (evento) => {
    const gatilho = evento.target.closest("[data-abrir]");
    if (gatilho) {
      if (abrirModal(gatilho.dataset.abrir, { ...gatilho.dataset })) evento.preventDefault();
      return;
    }
    const fechar = evento.target.closest("[data-fechar]");
    if (fechar) fechar.closest("dialog").close();
  });

  document.querySelectorAll("dialog.modal").forEach((modal) => {
    modal.tabIndex = -1;
    // Clique no fundo escurecido, fora da caixa, fecha o pop-up.
    modal.addEventListener("click", (evento) => {
      if (evento.target === modal) modal.close();
    });
  });

  document.querySelectorAll("[data-carrossel]").forEach(iniciarCarrossel);

  // Fotos da frota: só as que existem (lista gerada por src/site/otimizar_imagens.py), e só quando
  // o pop-up da frota abre pela primeira vez. Assim o site não pede arquivos que dariam erro 404.
  const fotosDisponiveis = window.FOTOS_FROTA || [];
  preparadores["modal-frota"] = () => {
    document.querySelectorAll("#modal-frota img[data-src]").forEach((foto) => {
      const chave = foto.dataset.src.split("/").pop().replace(".jpg", "");
      if (foto.dataset.pedida || !fotosDisponiveis.includes(chave)) return;
      foto.dataset.pedida = "sim";
      foto.addEventListener("load", () => {
        foto.closest("figure").hidden = false;
      }, { once: true });
      foto.src = foto.dataset.src;
    });
    return null;
  };
}

// ---------- Animação do topo e botão "Pausar animação" ----------
// O vídeo só carrega em telas largas, sem "economia de dados" e sem "reduzir movimento"; nos outros
// casos fica a foto. O botão pausa tudo que se mexe sozinho no topo (vídeo, foto e letreiro).

function iniciarAnimacaoTopo() {
  const topo = document.querySelector(".hero");
  const video = document.querySelector(".hero-video");
  const botao = document.querySelector("[data-pausar-movimento]");
  if (!topo || !botao) return;

  let pausado = false;
  const economiaDeDados = Boolean(navigator.connection && navigator.connection.saveData);
  // 60rem = 960 px: computadores e tablets deitados; celulares e tablets em pé ficam com a foto.
  const comVideo = Boolean(video) && !movimentoReduzido && !economiaDeDados && window.matchMedia("(min-width: 60rem)").matches;
  const tocar = () => { if (comVideo && !pausado) video.play().catch(() => {}); };

  if (comVideo) {
    // Com vídeo, a foto de baixo fica parada no enquadramento do primeiro quadro (sem o zoom lento).
    topo.classList.add("com-video");
    video.muted = true;
    video.loop = true;
    video.src = video.dataset.src;
    // Some 0,7 s antes do fim de cada volta e reaparece no recomeço: por baixo fica a foto,
    // que é igual ao primeiro quadro, então a repetição não tem corte seco.
    video.addEventListener("timeupdate", () => {
      video.classList.toggle("visivel", video.duration - video.currentTime >= 0.7);
    });
    // Fora da tela, o vídeo para (economiza processamento); volta quando o topo reaparece.
    if ("IntersectionObserver" in window) {
      new IntersectionObserver(([entrada]) => {
        if (entrada.isIntersecting) tocar();
        else video.pause();
      }).observe(topo);
    } else {
      tocar();
    }
  }

  botao.addEventListener("click", () => {
    pausado = !pausado;
    botao.setAttribute("aria-pressed", String(pausado));
    botao.querySelector("[data-pausar-rotulo]").textContent = pausado ? "Retomar animação" : "Pausar animação";
    document.documentElement.classList.toggle("movimento-pausado", pausado);
    if (comVideo) {
      if (pausado) video.pause();
      else tocar();
    }
  });
}

// ---------- Imagem ampliada dentro do pop-up (mural de 2016) ----------
// O link data-ampliar abre a imagem numa camada por cima do pop-up; sem JavaScript, abre a imagem numa aba.

function criarCamadaAmpliacao(modal) {
  const camada = document.createElement("div");
  camada.className = "ampliacao";
  camada.hidden = true;
  camada.innerHTML = `
    <img alt="">
    <div class="ampliacao-acoes">
      <a class="botao botao-vidro" target="_blank" rel="noopener">Abrir em tamanho real</a>
      <button class="botao" type="button">Fechar</button>
    </div>`;
  const fechar = () => {
    camada.hidden = true;
    if (camada.gatilho) camada.gatilho.focus();
  };
  camada.querySelector("button").addEventListener("click", fechar);
  camada.addEventListener("click", (evento) => {
    if (evento.target === camada) fechar();
  });
  // Esc fecha primeiro a imagem ampliada, e só depois o pop-up. A tecla é interceptada antes
  // de chegar ao pop-up (fase de captura), porque o Chrome nem sempre deixa cancelar o "cancel".
  modal.addEventListener("keydown", (evento) => {
    if (evento.key !== "Escape" || camada.hidden) return;
    evento.preventDefault();
    evento.stopPropagation();
    fechar();
  }, true);
  modal.addEventListener("cancel", (evento) => {
    if (!camada.hidden) evento.preventDefault();
  });
  modal.addEventListener("close", () => { camada.hidden = true; });
  modal.append(camada);
  return camada;
}

function iniciarAmpliacao() {
  document.querySelectorAll("[data-ampliar]").forEach((gatilho) => {
    gatilho.addEventListener("click", (evento) => {
      const modal = gatilho.closest("dialog");
      if (!modal || !modal.open) return;
      evento.preventDefault();
      const foto = gatilho.closest("figure").querySelector("img");
      const camada = modal.querySelector(".ampliacao") || criarCamadaAmpliacao(modal);
      const imagem = camada.querySelector("img");
      imagem.src = foto.currentSrc || foto.src;
      imagem.alt = foto.alt;
      camada.querySelector("a").href = gatilho.href;
      camada.gatilho = gatilho;
      camada.hidden = false;
      camada.querySelector("button").focus();
    });
  });
}

// ---------- Menu no celular ----------

function iniciarMenu() {
  const botao = document.querySelector(".topo-menu");
  const menu = document.getElementById("menu");
  if (!botao || !menu) return;

  const abrirOuFechar = (abrir) => {
    botao.setAttribute("aria-expanded", String(abrir));
    menu.classList.toggle("aberto", abrir);
  };

  botao.addEventListener("click", () => abrirOuFechar(botao.getAttribute("aria-expanded") !== "true"));
  menu.addEventListener("click", (evento) => {
    if (evento.target.closest("a")) abrirOuFechar(false);
  });
  document.addEventListener("keydown", (evento) => {
    if (evento.key === "Escape" && menu.classList.contains("aberto")) {
      abrirOuFechar(false);
      botao.focus();
    }
  });
}

// ---------- Pedido de orçamento: passo 1 (máquina e simulação), passo 2 (dados), passo 3 (pronto) ----------

function modalidadePorDias(dias) {
  // Mesmas faixas de src/gerador_dados/gerar_contratos_locacao.py (Diária 1-6, Semanal 7-28, Mensal 30+).
  if (dias <= 6) return "Diária";
  if (dias < 30) return "Semanal";
  return "Mensal";
}

function contatoValido(valor) {
  if (valor.includes("@")) return /^\S+@\S+\.\S+$/.test(valor);
  return valor.replace(/\D/g, "").length >= 10;
}

function iniciarPedido() {
  const modal = document.getElementById("modal-orcamento");
  const form = document.querySelector("[data-form-orcamento]");
  if (!modal || !form) return;

  const trilho = form.querySelector("[data-passos]");
  const passos = [...trilho.children];
  const textoPasso = modal.querySelector("[data-passo-texto]");
  const barra = modal.querySelector("[data-progresso]");
  const status = form.querySelector(".form-status");
  const saida = (nome) => form.querySelector(`[data-sim="${nome}"]`);
  const campos = form.elements;
  const textos = ["Passo 1 de 2: a máquina e o prazo.", "Passo 2 de 2: seus dados para a proposta.", "Pronto!"];
  let atual = 0;
  let simulacao = null;

  // A caixa dos passos acompanha a altura do passo visível (a confirmação é bem mais baixa).
  const caixa = trilho.parentElement;
  const ajustarAltura = () => {
    const altura = passos[atual].offsetHeight;
    caixa.style.height = altura ? `${altura}px` : "";
  };
  if ("ResizeObserver" in window) {
    const observador = new ResizeObserver(ajustarAltura);
    passos.forEach((passo) => observador.observe(passo));
  }

  function irParaPasso(indice) {
    atual = indice;
    trilho.style.transform = `translateX(${-100 * indice}%)`;
    // inert impede o Tab de entrar nos passos que estão fora da tela.
    passos.forEach((passo, i) => { passo.inert = i !== indice; });
    textoPasso.textContent = textos[indice];
    barra.style.width = `${[50, 100, 100][indice]}%`;
    ajustarAltura();
  }

  function simular() {
    const dias = Number(campos.dias.value);
    const horasDia = Number(campos.horas_dia.value);
    const horas = dias * horasDia;
    const revisoes = Math.floor(horas / INTERVALO_PREVENTIVA_HORAS);
    // Consumo e tanque de cada máquina ficam nos data-* dos slides da Frota.
    const ficha = document.querySelector(`.maquina[data-nome="${campos.equipamento.value}"]`);
    simulacao = { dias, horasDia, horas, modalidade: modalidadePorDias(dias) };

    saida("dias").textContent = dias === 1 ? "1 dia" : `${dias} dias`;
    saida("horas").textContent = `${horasDia} h`;
    saida("total").textContent = numeroBR.format(horas);
    saida("modalidade").textContent = simulacao.modalidade;
    saida("revisoes").textContent = revisoes === 0 ? "nenhuma" : numeroBR.format(revisoes);
    if (ficha) {
      const litros = horas * Number(ficha.dataset.consumo);
      saida("diesel").textContent = `${numeroBR.format(litros)} L`;
      saida("tanques").textContent = `cerca de ${numeroBR.format(Math.ceil(litros / Number(ficha.dataset.tanque)))}`;
    } else {
      saida("diesel").textContent = "escolha a máquina";
      saida("tanques").textContent = "—";
    }
  }

  function acrescentarObservacao(texto) {
    const campo = campos.observacao;
    if (campo.value.includes(texto)) return;
    campo.value = campo.value.trim() ? `${campo.value.trim()}\n${texto}` : texto;
  }

  [campos.equipamento, campos.dias, campos.horas_dia].forEach((campo) => campo.addEventListener("input", simular));

  form.querySelector("[data-avancar]").addEventListener("click", () => {
    if (!campos.equipamento.reportValidity()) return;
    irParaPasso(1);
    ([campos.nome, campos.contato].find((campo) => !campo.value.trim()) || campos.cidade).focus({ preventScroll: true });
  });
  form.querySelector("[data-voltar]").addEventListener("click", () => {
    irParaPasso(0);
    campos.equipamento.focus({ preventScroll: true });
  });

  campos.contato.addEventListener("input", () => {
    const valor = campos.contato.value.trim();
    campos.contato.setCustomValidity(valor && !contatoValido(valor) ? "Informe um e-mail ou um telefone com DDD." : "");
  });

  preparadores["modal-orcamento"] = (dados) => {
    if (atual === 2) form.reset();
    status.hidden = true;
    if (dados.equipamento) campos.equipamento.value = dados.equipamento;
    if (dados.observacao) acrescentarObservacao(dados.observacao);
    irParaPasso(0);
    simular();
    return campos.equipamento;
  };

  function mostrarSucesso(nome, resumo) {
    form.querySelector("[data-sucesso-texto]").textContent =
      URL_APPS_SCRIPT
        ? `Obrigado, ${nome}! Seu pedido foi enviado. Como este site é uma demonstração, ninguém vai entrar em contato.`
        : `Obrigado, ${nome}! Pedido registrado em modo de teste: os dados só aparecem no console do navegador (F12).`;
    form.querySelector("[data-sucesso-resumo]").replaceChildren(...resumo.map(([rotulo, valor]) => {
      const item = document.createElement("li");
      item.append(`${rotulo}: `);
      const forte = document.createElement("strong");
      forte.textContent = valor;
      item.append(forte);
      return item;
    }));
    irParaPasso(2);
    passos[2].focus();
  }

  form.addEventListener("submit", async (evento) => {
    evento.preventDefault();
    const s = simulacao;
    campos.prazo.value = `${s.modalidade}, ${s.dias} dias`;
    const dados = Object.fromEntries(new FormData(form));

    // Robôs preenchem o campo-isca; pessoas não o veem. Finge sucesso e não envia nada.
    if (dados.site) {
      mostrarSucesso(dados.nome, []);
      return;
    }
    delete dados.site;
    delete dados.dias;
    delete dados.horas_dia;
    dados.observacao = [dados.observacao.trim(), `Simulação no site: ${s.dias} dias × ${s.horasDia} h/dia = ${numeroBR.format(s.horas)} h de uso.`]
      .filter(Boolean)
      .join("\n");
    dados.origem = "site";
    console.log("Pedido de orçamento (LocaMaq):", dados);

    const resumo = [["Máquina", dados.equipamento], ["Prazo", dados.prazo], ["Uso estimado", `${numeroBR.format(s.horas)} h`]];
    if (!URL_APPS_SCRIPT) {
      mostrarSucesso(dados.nome, resumo);
      return;
    }

    const botao = form.querySelector('[type="submit"]');
    botao.disabled = true;
    botao.textContent = "Enviando...";
    try {
      // O Apps Script não devolve os cabeçalhos que o navegador exige para ler a resposta (CORS).
      // "no-cors" envia mesmo assim; a confirmação de verdade é a linha nova na planilha.
      await fetch(URL_APPS_SCRIPT, { method: "POST", mode: "no-cors", body: new URLSearchParams(dados) });
      mostrarSucesso(dados.nome, resumo);
    } catch (erro) {
      console.error("Falha no envio do pedido:", erro);
      status.textContent = "Não foi possível enviar agora. Confira a internet e tente de novo, ou ligue para a unidade.";
      status.hidden = false;
    } finally {
      botao.disabled = false;
      botao.textContent = "Enviar pedido";
    }
  });

  irParaPasso(0);
  simular();
}

// ---------- Movimento: entradas ao rolar e contadores ----------

function iniciarEntradas() {
  const elementos = document.querySelectorAll("[data-entrada]");
  if (movimentoReduzido || !("IntersectionObserver" in window)) {
    elementos.forEach((elemento) => elemento.classList.add("visivel"));
    document.documentElement.classList.add("anima-ok");
    return;
  }

  const observador = new IntersectionObserver((entradas) => {
    let ordem = 0;
    entradas.forEach((entrada) => {
      if (!entrada.isIntersecting) return;
      entrada.target.style.setProperty("--ordem", ordem++);
      entrada.target.classList.add("visivel");
      observador.unobserve(entrada.target);
    });
  }, { rootMargin: "0px 0px -6% 0px", threshold: 0.12 });

  elementos.forEach((elemento) => observador.observe(elemento));
  document.documentElement.classList.add("anima-ok");
}

function contar(elemento) {
  const final = Number(elemento.dataset.contar);
  const duracao = 1400;
  const inicio = performance.now();
  function passo(agora) {
    const progresso = Math.min((agora - inicio) / duracao, 1);
    const suavizado = 1 - Math.pow(1 - progresso, 3);
    elemento.textContent = numeroBR.format(Math.round(final * suavizado));
    if (progresso < 1) requestAnimationFrame(passo);
  }
  requestAnimationFrame(passo);
}

function iniciarContadores() {
  if (movimentoReduzido || !("IntersectionObserver" in window)) return;
  const observador = new IntersectionObserver((entradas) => {
    entradas.forEach((entrada) => {
      if (!entrada.isIntersecting) return;
      observador.unobserve(entrada.target);
      contar(entrada.target);
    });
  }, { threshold: 0.6 });

  document.querySelectorAll("[data-contar]").forEach((elemento) => {
    elemento.textContent = "0";
    observador.observe(elemento);
  });
}

// ---------- Início ----------

iniciarEntradas();
iniciarAnimacaoTopo();
preencherContatos();
iniciarModais();
iniciarAmpliacao();
iniciarMenu();
iniciarPedido();
iniciarContadores();
