import {filtered, indicators, pairedComparison, longitudinal, socioeconomic} from '../domain/analysis.js';

// Caso de uso: aplica filtros de escola/turma às duas bases e categoria só aos gráficos.
export function dashboardView(data, filters) {
  const vocab = filtered(data.vocab, filters.school, filters.classroom);
  const tde = filtered(data.tde, filters.school, filters.classroom);
  const selected = filters.category === 'tde' ? tde : vocab;
  return {
    indicators: indicators(vocab,tde),
    comparison: pairedComparison(selected),
    longitudinal: longitudinal(selected),
    socioeconomic: socioeconomic(selected,filters.dimension),
    selectedCount:selected.length,
    category:filters.category
  };
}
