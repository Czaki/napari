from pathlib import Path

import pooch
from skimage.data import data_dir

try:
    from nilearn import datasets
except ImportError:
    datasets = None

data_path = Path(data_dir)

data_path.mkdir(parents=True, exist_ok=True)

data_files = {
    'cells3d.tif': 'md5:4a427a79f339b4ef9a3a71993d8e0b22',
    'lily.tif': 'sha256:395c2f0194c25b9824a8cd79266920362a0816bc9e906dd392adce2d8309af03',
    'pivchallenge-B-B001_1.tif': 'sha256:e95e09abbcecba723df283ac7d361766328abd943701a2ec2f345d4a2014da2a',
    'pivchallenge-B-B001_2.tif': 'sha256:4ceb5407e4e333476a0f264c14b7a3f6c0e753fcdc99ee1c4b8196e5f823805e',
}


def prefetch_data():
    for filename, known_hash in data_files.items():
        if not (data_path / filename).exists():
            pooch.retrieve(
                url=f'https://data.napari.dev/examples/{filename}',
                path=data_path,
                fname=filename,
                known_hash=known_hash,
            )
    if datasets is not None:
        datasets.fetch_surf_nki_enhanced(
            n_subjects=1,
            url='https://data.napari.dev/examples/',
        )



if __name__ == "__main__":
    prefetch_data()
