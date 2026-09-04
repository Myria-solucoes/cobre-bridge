# NEWAVE study and post-study horizons

A converted NEWAVE case can contain more computational stages than the period
whose results an analyst should normally evaluate. The source deck separates:

- the **study period**, declared by `num_anos_estudo`, where operational results
  are analyzed; and
- the **post-study period**, declared by `num_anos_pos_estudo`, which extends the
  optimization so a zero terminal future-cost function does not distort the end
  of the study period.

The bridge keeps both periods as Cobre stages because removing the post-study
tail without an equivalent terminal future-cost function changes the policy.
It also records their boundary in `conversion_manifest.json`:

```json
{
  "horizon": {
    "study_stage_count": 57,
    "post_study_stage_count": 60,
    "total_stage_count": 117,
    "first_post_study_stage_id": 57
  }
}
```

Stage ids are zero-based. In this example, ids 0 through 56 belong to the study
period and ids 57 through 116 belong to the post-study period.

Consumers should use the fields as follows:

```python
import json
from pathlib import Path

manifest = json.loads(Path("converted-case/conversion_manifest.json").read_text())
horizon = manifest["horizon"]
study_stage_ids = range(horizon["study_stage_count"])
post_study_stage_ids = range(
    horizon["first_post_study_stage_id"],
    horizon["total_stage_count"],
)
```

Present the study period by default in analytical tables and charts. The
post-study period may remain available behind an explicit filter, labelled as
auxiliary. Do not discard it from the solver input or training horizon.

For a DECOMP conversion, every emitted stage is part of the study period:
`post_study_stage_count` is zero and `first_post_study_stage_id` is `null`.

Manifests written by earlier bridge versions omit `horizon`. Readers must remain
backward compatible; without another authoritative source, they should describe
such a case as an unclassified computational horizon rather than guess a study
boundary.
