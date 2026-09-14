# Large-scale offline builds

BioCypher normally keeps identifiers in memory while it deduplicates nodes and
edges. For datasets that are too large for this approach, enable `big_data` to
use disk-backed deduplication.

## Requirements

Large-scale deduplication is an optional feature. Install its dependencies
before running a build:

```bash
uv add "biocypher[bigdata]"
# or: pip install "biocypher[bigdata]"
```

This installs `xxhash`, `lmdb`, and `rbloom`.

`big_data` is supported only in offline mode. It cannot be used to write to a
running database or an in-memory graph.

## Enable disk-backed deduplication

Set `big_data` alongside `offline: true` in `biocypher_config.yaml`:

```yaml
biocypher:
  dbms: neo4j
  offline: true
  big_data: true
```

Alternatively, enable it when creating the BioCypher instance:

```python
from biocypher import BioCypher

bc = BioCypher(offline=True, big_data=True)
```

Using `big_data=True` with `offline=False` raises a `ValueError`.

## Deduplication behaviour

Disk-backed deduplication has the same behaviour as BioCypher's standard
in-memory deduplicator.

## Resource planning

The default Bloom filter is sized for one billion identifiers with a false
positive rate of `0.00001`. It uses approximately 2.8 GiB of RAM. LMDB stores
hashed identifiers on disk; its actual disk use grows with the number of
identifiers processed.

The LMDB database is created in a temporary directory and is an implementation
detail of a single build. Do not rely on it as a persistent index. Ensure that
the system temporary directory has sufficient free space for the build.

If the dataset fits comfortably in memory, leave `big_data` disabled: the
standard in-memory deduplicator has less overhead.

## How it works

The disk-backed deduplicator keeps duplicate detection scalable through three
layers:

1. A small in-memory set contains identifiers from the current batch.
2. A Bloom filter rejects identifiers that have definitely not been seen.
3. An LMDB database authoritatively records the identifiers that have been
   seen.

The pending identifiers are written to LMDB in batches of 100,000. A positive
Bloom-filter match is always checked against LMDB, so Bloom-filter false
positives add a disk lookup but do not cause data to be discarded.
