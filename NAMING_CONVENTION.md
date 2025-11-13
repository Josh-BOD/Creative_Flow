# 📝 Creative Asset Naming Convention

## Updated Format (November 13, 2025)

### Regular Files
```
{Language}_{Category}_{ModelSex}_{Style}_{Rating}_{Type}_{Creator}_{Duration}sec_T-{TestID}_ID-{UniqueID}.ext
```

### Native Files
```
VID_{Language}_{Category}_{ModelSex}_{Style}_{Rating}_{Type}_{Creator}_{Duration}sec_T-{TestID}_ID-{UniqueID}-VID.mp4
IMG_{Language}_{Category}_{ModelSex}_{Style}_{Rating}_{Type}_{Creator}_T-{TestID}_ID-{UniqueID}-IMG.png
```

### Native Originals
```
ORG_{Language}_{Category}_{ModelSex}_{Style}_{Rating}_{Type}_{Creator}_{Duration}sec_T-{TestID}_ID-{UniqueID}.mp4
```

---

## 🔤 Field Definitions

| Field | Description | Examples | Required |
|-------|-------------|----------|----------|
| **Language** | 2-letter language code | `EN`, `ES`, `FR`, `JP` | ✅ Yes |
| **Category** | Content category | `Ahegao`, `Hentai`, `Blondie` | ✅ Yes |
| **ModelSex** | Model gender/sex | `M`=Male, `F`=Female, `T`=Trans, `MFT`=All | ✅ Yes |
| **Style** | Creative style | `Anime`, `Real`, `Both` | ✅ Yes |
| **Rating** | Content rating | `NSFW`, `SFW` | ✅ Yes |
| **Type** | Creative description | `Generic`, `Special`, `Custom` | ✅ Yes |
| **Creator** | Creator name | `Seras`, `Pedro`, `Maria` | ✅ Yes |
| **Duration** | Video length (seconds) | `5sec`, `15sec`, `30sec` | Videos only |
| **TestID** | Test identifier | `001`, `002`, `ABC` | ❌ Optional |
| **UniqueID** | System-generated ID | `ID-F40623FA` | ✅ Yes |

---

## 📋 Examples

### Regular Video (WITH Test ID)
```
EN_Ahegao_F_Anime_NSFW_Generic_Seras_5sec_T-001_ID-F40623FA.mp4
│  │      │ │     │    │       │     │    │     │
│  │      │ │     │    │       │     │    │     └─ Unique ID
│  │      │ │     │    │       │     │    └─ Test ID (001)
│  │      │ │     │    │       │     └─ Duration (5 seconds)
│  │      │ │     │    │       └─ Creator (Seras)
│  │      │ │     │    └─ Creative Type (Generic)
│  │      │ │     └─ Content Rating (NSFW)
│  │      │ └─ Style (Anime)
│  │      └─ Model Sex (Female)
│  └─ Category (Ahegao)
└─ Language (English)
```

### Regular Video (NO Test ID)
```
EN_Blondie_F_Real_NSFW_Generic_Seras_8sec_ID-D0BB8AFA.mp4
```

### Regular Image
```
EN_Cumshot_MFT_Both_NSFW_Generic_Seras_T-002_ID-A1B2C3D4.jpg
```

### Native Video Pair
```
VID_EN_BigBoobs_F_Anime_NSFW_Generic_Seras_4sec_T-003_ID-1A2B3C4D-VID.mp4
IMG_EN_BigBoobs_F_Anime_NSFW_Generic_Seras_T-003_ID-1A2B3C4D-IMG.png
```
*Note: Both video and image share the same base ID (`ID-1A2B3C4D`)*

### Native Original (Source)
```
ORG_EN_Cumshot_MFT_Both_NSFW_Generic_Seras_12sec_T-001_ID-9F8E7D6C.mp4
```
*This is the original source file before native conversion*

---

## 🗂️ File Organization

### Output Structure
```
uploaded/
├── EN_Ahegao_F_Anime_NSFW_Generic_Seras_5sec_T-001_ID-F40623FA.mp4
├── EN_Blondie_F_Real_NSFW_Generic_Seras_8sec_ID-D0BB8AFA.mp4
└── Native/
    ├── Video/
    │   └── VID_EN_BigBoobs_F_Anime_NSFW_Generic_Seras_4sec_T-003_ID-1A2B3C4D-VID.mp4
    └── Image/
        └── IMG_EN_BigBoobs_F_Anime_NSFW_Generic_Seras_T-003_ID-1A2B3C4D-IMG.png
```

---

## ⚙️ Configuration

Test IDs and other metadata are configured in `tracking/metadata_defaults.csv`:

```csv
folder_path,category_name,model_sex,style,creator_name,language,content_type,creative_description,test_id
Hentai,Hentai,F,Anime,Seras,EN,NSFW,Generic,
Blondie,Blondie,F,Real,Seras,EN,NSFW,Generic,001
Massive Breasts,Big Boobs,F,Anime,Seras,EN,NSFW,Generic,002
```

- **Empty `test_id`** = No test ID in filename
- **Filled `test_id`** = Adds `T-{value}` to filename

---

## 🎯 Key Features

1. **Model Sex Field**: Distinguish between Male, Female, Trans, or All content
2. **Style Field**: Separate Anime vs Real vs Both creative styles  
3. **Test ID**: Optional field for A/B testing and campaign tracking
4. **Standardized Categories**: Map multiple folder names to canonical categories
5. **Native Support**: Dedicated structure for 640x360 native video/image pairs
6. **Unique IDs**: System-generated 8-character hex IDs for tracking

---

## 📝 Notes

- Test IDs are **optional** - leave blank in CSV if not needed
- Native videos are always **4 seconds** at **640x360** resolution
- Native images are **PNG format**, compressed to **<300KB** (decimal)
- Original source videos get `ORG_` prefix before native conversion
- All special characters are sanitized (removed) from filenames
- Video durations are rounded to nearest second

---

**Last Updated:** November 13, 2025  
**System Version:** Creative Flow v2.0

