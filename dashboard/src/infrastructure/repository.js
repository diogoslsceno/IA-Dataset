// Adaptador de dados: duas fontes independentes, carregadas em paralelo.
export async function loadDatasets() {
  const [vocab, tde] = await Promise.all(['vocabulario','tde'].map(async category => {
    const response = await fetch(`data/${category}.json`);
    if (!response.ok) throw new Error(`Falha ao carregar ${category}: HTTP ${response.status}`);
    return response.json();
  }));
  return {vocab,tde};
}
