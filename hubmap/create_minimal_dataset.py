#!/usr/bin/env python

from typing import List
from pathlib import Path
from argparse import ArgumentParser
import pandas as pd

if __name__ == '__main__':
    import django

    django.setup()


def make_mini_cell_df(file):
    with pd.HDFStore(file) as store:
        cell_df = store.get('cell')
        mini_cell_df = cell_df.head(1000).copy()
        if 'cell_id' not in mini_cell_df.columns:
            mini_cell_df['cell_id'] = mini_cell_df.index
        cell_ids = list(mini_cell_df['cell_id'].unique())

    new_file = 'mini_' + file.stem + '.hdf5'
    with pd.HDFStore(new_file) as store:
        if file.stem == 'codex':
            store.put('cell', mini_cell_df)
        else:
            store.put('cell', mini_cell_df, format='t')

    return cell_ids


def make_mini_quant_df(file, cell_ids):

    with pd.HDFStore(file) as store:
        genes = list(store.get('quant').columns)[:1000]
        chunks = len(store.get('quant').index) // 1000 + 1
        filtered_chunks = []

        for i in range(chunks):
            print('Loading chunk ' + str(i) + ' out of ' + str(chunks))
            chunk = store.select('quant', start=i * 1000, stop=(i + 1) * 1000)
            filtered_chunk = chunk[genes]
            empty = True
            print(cell_ids[0])
            for i in chunk.index:
                if i in cell_ids:
                    empty = False
            if not empty:
                filtered_chunk = filtered_chunk[cell_ids]
                filtered_chunks.append(filtered_chunk)

    filtered_quant_df = pd.concat(filtered_chunks)
    new_file = 'mini_' + file.stem + '.hdf5'
    with pd.HDFStore(new_file) as store:
        store.put('quant', filtered_quant_df)

    return genes

def make_mini_pval_df(file, gene_ids):

    with pd.HDFStore(file) as store:
        pval_df = store.get('p_values')
        pval_df = pval_df.set_index('gene_id', drop=False)
        filtered_pval_df = pval_df.loc[gene_ids]

    new_file = 'mini_' + file.stem + '.hdf5'
    with pd.HDFStore(new_file) as store:
        store.put('p_values', filtered_pval_df)

    return


def main(hdf_files: List[Path]):

    for file in hdf_files:
        cell_ids = make_mini_cell_df(file)
        if file.stem in ['atac', 'rna']:
            gene_ids = make_mini_quant_df(file, cell_ids)
            make_mini_pval_df(file, gene_ids)



if __name__ == '__main__':
    p = ArgumentParser()
    p.add_argument('hdf_files', type=Path, nargs='+')
    args = p.parse_args()

    main(args.hdf_files)
