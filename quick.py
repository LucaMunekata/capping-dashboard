import pandas as pd

# Caminho para o arquivo CSV
arquivo_csv = 'data/planilha_apostas.csv'
new = 'data/planilha_apostas_new.csv'

# Carrega o CSV
df = pd.read_csv(arquivo_csv)

# Verifica se a coluna 'parlay' existe
if 'parlay' not in df.columns:
    raise ValueError("A coluna 'parlay' não foi encontrada no CSV.")

# Verifica se a coluna 'unidade_vigente' existe
if 'unidade_vigente' not in df.columns:
    # Se não existir, cria a coluna 'unidade_vigente' e preenche com NaN
    df['unidade_vigente'] = None

# Atribui 10.00 onde parlay == 'N'
df.loc[df['parlay'] == 'N', 'unidade_vigente'] = 10.00

# Salva o CSV atualizado
df.to_csv(new, index=False)

print("Coluna 'unidade_vigente' atualizada com sucesso!")
