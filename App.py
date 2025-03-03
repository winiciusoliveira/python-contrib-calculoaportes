import tkinter as tk
from tkinter import messagebox, ttk
import json
import ttkbootstrap as tb
import csv

# Nome do arquivo de configuração
CONFIG_FILE = "aporte_config.json"
EXCEL_FILE = "posicao.xlsx"


def salvar_config():
    """ Salva os valores atuais da interface no arquivo JSON. """
    dados = {
        "patrimonio_atual": converter_float(entry_patrimonio.get()),
        "aporte": converter_float(entry_aporte.get()),
        "percentual_atual": {classe: formatar_percentual(converter_percentual(entries_atual[classe].get()))
                             for classe in entries_atual},
        "percentual_ideal": {classe: formatar_percentual(converter_percentual(entries_ideal[classe].get()))
                             for classe in entries_ideal}
    }
    with open(CONFIG_FILE, "w", encoding="utf-8") as f:
        json.dump(dados, f, indent=4, ensure_ascii=False)
    messagebox.showinfo("Sucesso", "Configurações salvas com sucesso!")


def validar_config(dados):
    """ Garante que os dados carregados tenham a estrutura correta. """
    chaves_principais = {"patrimonio_atual", "aporte", "percentual_atual", "percentual_ideal"}
    if not all(chave in dados for chave in chaves_principais):
        return False
    if not isinstance(dados["percentual_atual"], dict) or not isinstance(dados["percentual_ideal"], dict):
        return False
    return True


def carregar_config():
    """ Carrega os dados do arquivo JSON ou retorna valores padrão. """
    dados_padrao = {
        "patrimonio_atual": 790.47,
        "aporte": 819.0,
        "percentual_atual": {
            "Ações": "55.35%",
            "Exterior": "34.97%",
            "ETFs": "0.00%",
            "FIIs": "25.00%",
            "Renda Fixa": "0.00%",
            "Criptomoedas": "1.58%"
        },
        "percentual_ideal": {
            "Ações": "0.00%",
            "Exterior": "0.00%",
            "ETFs": "0.00%",
            "FIIs": "50.00%",
            "Renda Fixa": "50.00%",
            "Criptomoedas": "0.00%"
        }
    }
    try:
        with open(CONFIG_FILE, "r", encoding="utf-8") as f:
            dados = json.load(f)
            if not validar_config(dados):
                return dados_padrao
        return dados
    except (FileNotFoundError, json.JSONDecodeError):
        return dados_padrao


def converter_percentual(valor):
    """ Converte string percentual 'XX.XX%' para float (0.XX), garantindo robustez contra valores inesperados. """
    if isinstance(valor, float) or isinstance(valor, int):
        return valor / 100 if valor > 1 else valor  # Se for um número e maior que 1, assume que precisa ser dividido por 100
    try:
        return float(valor.replace("%", "").replace(",", ".")) / 100
    except (ValueError, AttributeError):
        return 0.0  # Retorna 0.0 caso o valor seja inválido


def formatar_percentual(valor):
    """ Converte float (0.XX) para string percentual 'XX.XX%'. """
    return f"{valor * 100:.2f}%"


def calcular_aporte(patrimonio_atual, aporte, percentual_atual, percentual_ideal):
    """ Calcula a melhor alocação do aporte. """
    valor_atual = {classe: patrimonio_atual * percentual for classe, percentual in percentual_atual.items()}
    valor_ideal = {classe: (patrimonio_atual + aporte) * percentual for classe, percentual in percentual_ideal.items()}
    diferenca = {classe: valor_ideal[classe] - valor_atual.get(classe, 0) for classe in percentual_ideal}

    total_diferenca_positiva = sum(v for v in diferenca.values() if v > 0)
    if total_diferenca_positiva == 0:
        return {classe: 0 for classe in diferenca}

    return {classe: (diferenca[classe] / total_diferenca_positiva) * aporte if diferenca[classe] > 0 else 0 for classe
            in diferenca}


def converter_float(valor):
    """ Converte strings para float, tratando erros e substituindo vírgula por ponto. """
    try:
        return float(str(valor).replace(",", "."))
    except ValueError:
        return 0.0


def soma_percentuais(percentuais):
    """ Soma os valores percentuais para validar se ultrapassam 100%. """
    return sum(converter_percentual(valor) for valor in percentuais.values())


def calcular_e_exibir():
    """ Obtém os valores da interface, valida, calcula e exibe os resultados. """
    patrimonio_atual = converter_float(entry_patrimonio.get())
    aporte = converter_float(entry_aporte.get())

    percentual_atual = {classe: converter_percentual(entries_atual[classe].get()) for classe in entries_atual}
    percentual_ideal = {classe: converter_percentual(entries_ideal[classe].get()) for classe in entries_ideal}

    if soma_percentuais(percentual_ideal) > 1.0:
        messagebox.showerror("Erro", "A soma dos percentuais ideais ultrapassa 100%. Ajuste os valores.")
        return

    aportes_sugeridos = calcular_aporte(patrimonio_atual, aporte, percentual_atual, percentual_ideal)
    atualizar_tabela(aportes_sugeridos)

    # Converter de volta para formato percentual antes de salvar
    # dados = {
    #     "patrimonio_atual": patrimonio_atual,
    #     "aporte": aporte,
    #     "percentual_atual": {classe: formatar_percentual(percentual_atual[classe]) for classe in percentual_atual},
    #     "percentual_ideal": {classe: formatar_percentual(percentual_ideal[classe]) for classe in percentual_ideal}
    # }

    # salvar_config(dados)
    messagebox.showinfo("Sucesso", "Os valores foram calculados e salvos com sucesso!")


def atualizar_tabela(aportes):
    """ Atualiza a tabela de resultados e exibe o total alocado sem duplicar labels. """
    # Remover entradas antigas da tabela
    for row in tree.get_children():
        tree.delete(row)

    # Calcular total alocado
    total_alocado = sum(aportes.values())

    # Adicionar novos valores à tabela
    for classe, valor in aportes.items():
        tree.insert("", "end", values=(classe, f"R$ {valor:.2f}"))

    # Atualizar apenas o texto da label existente, sem criar uma nova
    label_total.config(text=f"Total Alocado: R$ {total_alocado:.2f}")


def exportar_csv():
    """ Exporta os resultados do cálculo para um arquivo CSV. """
    with open("resultado_aporte.csv", "w", newline="", encoding="utf-8") as f:
        writer = csv.writer(f)
        writer.writerow(["Classe", "Valor a Investir (R$)"])

        for row in tree.get_children():
            valores = tree.item(row, "values")
            writer.writerow(valores)

    messagebox.showinfo("Exportado", "Os resultados foram exportados para 'resultado_aporte.csv' com sucesso!")


def resetar_percentuais():
    """ Define os percentuais ideais para 100% divididos entre as classes."""
    classes = list(entries_ideal.keys())
    percentual_por_classe = 100 / len(classes)

    for classe in entries_ideal:
        entries_ideal[classe].delete(0, tk.END)
        entries_ideal[classe].insert(0, f"{percentual_por_classe:.2f}%")


def redefinir_valores():
    """ Restaura os valores padrão carregados do JSON. """
    dados = carregar_config()
    entry_patrimonio.delete(0, tk.END)
    entry_patrimonio.insert(0, dados["patrimonio_atual"])
    entry_aporte.delete(0, tk.END)
    entry_aporte.insert(0, dados["aporte"])

    for classe in entries_atual:
        entries_atual[classe].delete(0, tk.END)
        entries_atual[classe].insert(0, dados["percentual_atual"].get(classe, "0.00%"))
        entries_ideal[classe].delete(0, tk.END)
        entries_ideal[classe].insert(0, dados["percentual_ideal"].get(classe, "0.00%"))


def configurar_scroll(event):
    """ Permite rolagem com a roda do mouse. """
    canvas.yview_scroll(-1 * (event.delta // 120), "units")


# Criar a janela principal
root = tb.Window(themename="superhero")
root.title("Calculadora de Aporte")
root.geometry("1000x900")
root.resizable(False, False)

# Carregar dados de configuração
dados = carregar_config()

# Criar entradas e interface
frame_input = tb.Frame(root)
frame_input.pack(pady=20, padx=20, fill="both", expand=True)

canvas = tk.Canvas(frame_input)
scrollbar = ttk.Scrollbar(frame_input, orient="vertical", command=canvas.yview)

scrollable_frame = ttk.Frame(canvas)
scrollable_frame.bind("<Configure>", lambda e: canvas.configure(scrollregion=canvas.bbox("all")))

canvas.create_window((0, 0), window=scrollable_frame, anchor="nw")
canvas.configure(yscrollcommand=scrollbar.set)

frame_input.bind("<Enter>", lambda e: root.bind_all("<MouseWheel>", configurar_scroll))
frame_input.bind("<Leave>", lambda e: root.unbind_all("<MouseWheel>"))

canvas.pack(side="left", fill="both", expand=True)
scrollbar.pack(side="right", fill="y")

# Entradas
tb.Label(scrollable_frame, text="Patrimônio Atual:").grid(row=0, column=0, pady=10)
entry_patrimonio = tb.Entry(scrollable_frame, width=25)
entry_patrimonio.grid(row=0, column=1, pady=10)
entry_patrimonio.insert(0, dados["patrimonio_atual"])

tb.Label(scrollable_frame, text="Aporte Mensal:").grid(row=1, column=0, pady=10)

entry_aporte = tb.Entry(scrollable_frame, width=25)
entry_aporte.grid(row=1, column=1, pady=10)
entry_aporte.insert(0, dados["aporte"])

entries_atual = {}
entries_ideal = {}

# Adicionar espaço em Branco
tb.Label(scrollable_frame, text="").grid(row=1, column=1, pady=10)

for i, classe in enumerate(dados["percentual_atual"].keys()):
    tb.Label(scrollable_frame, text=classe).grid(row=i + 2, column=0, pady=10)
    entry_atual = tb.Entry(scrollable_frame, width=25)
    entry_atual.grid(row=i + 2, column=1, pady=10)
    entry_atual.insert(0, dados["percentual_atual"].get(classe, "0.00%"))
    entries_atual[classe] = entry_atual
    entry_ideal = tb.Entry(scrollable_frame, width=25)
    entry_ideal.grid(row=i + 2, column=2, pady=10)
    entry_ideal.insert(0, dados["percentual_ideal"].get(classe, "0.00%"))
    entries_ideal[classe] = entry_ideal

frame_botoes = tb.Frame(root)
frame_botoes.pack(pady=10)

tb.Button(frame_botoes, text="Calcular", command=calcular_e_exibir).pack(side="left", padx=5)
tb.Button(frame_botoes, text="Salvar Configurações", command=salvar_config).pack(side="left", padx=5)
tb.Button(frame_botoes, text="Redefinir Valores", command=redefinir_valores).pack(side="left", padx=5)
# tb.Button(root, text="Resetar para 100%", command=resetar_percentuais).pack(pady=10)
# tb.Button(root, text="Exportar CSV", command=exportar_csv).pack(pady=10)

tree = ttk.Treeview(root, columns=("Classe", "Valor"), show="headings")
tree.heading("Classe", text="Classe de Ativo")
tree.heading("Valor", text="Valor a Investir")
tree.pack(pady=10)

label_total = tb.Label(root, text="Total Alocado: R$ 0.00", font=("Arial", 12, "bold"))
label_total.pack(pady=10)

root.mainloop()
