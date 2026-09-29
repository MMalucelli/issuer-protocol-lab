from __future__ import annotations
import streamlit as st

OPERATIONS = {
    '+': 'soma', '-': 'subtração', '*': 'multiplicação', '/': 'divisão',
    '**': 'potência', 'sqrt(x)': 'raiz quadrada', 'exp(x)': 'exponencial eˣ',
    'log(x)': 'logaritmo natural', 'abs(x)': 'valor absoluto',
    'min(a,b)': 'menor valor', 'max(a,b)': 'maior valor',
    'clamp(x,a,b)': 'limita x ao intervalo [a,b]',
}

def expression_editor(label, key, variables, default, explanations=None, help_text=None):
    st.markdown(f'**{label}**')
    if help_text:
        st.caption(help_text)
    left, right = st.columns(2, gap='medium')
    with left:
        st.markdown('##### Variáveis disponíveis')
        for name in variables:
            desc = (explanations or {}).get(name, '')
            st.markdown(f'`{name}`  ·  {desc}' if desc else f'`{name}`')
    with right:
        st.markdown('##### Operações disponíveis')
        for op, desc in OPERATIONS.items():
            st.markdown(f'`{op}`  ·  {desc}')
    value = st.text_area('Função', value=st.session_state.get(key, default), key=f'{key}_editor', height=92)
    st.session_state[key] = value
    return value

# compatibility alias
expression_builder = expression_editor
