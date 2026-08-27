#!/bin/bash
# 写实化批产：每视图 2 候选并下载到 ai/out/<视图>-<序号>.png (bash 3.2 兼容)
# 用法: bash ai/gen_photoreal.sh [视图名...]   缺省跑全部5个
cd "$(dirname "$0")/.."; mkdir -p ai/out

P_BASE="转化为实景室内摄影照片：真实装修完成的书房，严格保持原图的空间布局、家具种类、位置尺寸与整体配色不变；呈现真实材质肌理——实木书架纹理与丰富书脊、真皮座椅皮革颗粒感、棉麻织物与羊毛地毯纤维；专业室内设计摄影，画面家具轮廓端正无变形无扭曲，8K细节"

prompt_for(){
  case "$1" in
    in1-overview-day)   echo "$P_BASE；午后阳光从南窗斜洒入室，窗外绿树景深虚化" ;;
    in2-shelf-day)      echo "$P_BASE；重点表现通顶书架上摆满的书籍细节与层次丰富的书脊色彩" ;;
    in3-window-day)     echo "$P_BASE；重点表现凸窗软垫坐榻阅读角，阳光洒在坐垫上" ;;
    in4-desk-night)     echo "转化为实景室内摄影照片：夜晚温馨书房实拍，严格保持原图空间布局、家具种类位置尺寸与配色不变；吊灯与绿罩台灯发出暖黄光晕，光影柔和呈琥珀色调，木质与皮革的真实肌理，画面无变形无扭曲，专业室内摄影8K" ;;
    in5-overview-green) echo "$P_BASE；深胡桃木配墨绿色背板的英伦风格书房，白天自然光" ;;
    *) echo "" ;;
  esac
}
download_one(){ # name idx url
  local out="ai/out/$1-$2.png"
  curl -sL --max-time 150 "$3" -o "$out"
  if [ -s "$out" ] && [ "$(stat -f%z "$out")" -gt 30000 ]; then echo "$1-$2 OK"; else echo "$1-$2 DL_FAIL"; fi
}
run_one(){
  local name=$1 img="ai/ref/$1.png" p json
  [ -f "$img" ] || { echo "$name NO_REF"; return; }
  p=$(prompt_for "$name"); [ -n "$p" ] || { echo "$name NO_PROMPT"; return; }
  echo "==== $name ===="
  json="/tmp/dm-$name.json"
  dreamina image2image --images "$img" --prompt="$p" --ratio="3:2" \
    --resolution_type=2k --model_version=5.0 --generate_num=2 --poll=420 \
    > "$json" 2>/dev/null || { echo "$name SUBMIT_FAIL"; return; }
  python3 -c "
import json,sys,subprocess,os
d=json.load(open(sys.argv[2]))
imgs=d.get('result_json',{}).get('images',[])
if not imgs: print(sys.argv[1],'NO_IMG'); sys.exit(0)
for i,im in enumerate(imgs): print('URL',sys.argv[1],i,im['image_url'])
" "$name" "$json" | while read -r _tag nm ix url; do download_one "$nm" "$ix" "$url"; done
}
if [ $# -gt 0 ]; then for n in "$@"; do run_one "$n"; done
else for n in in1-overview-day in2-shelf-day in3-window-day in4-desk-night in5-overview-green; do run_one "$n"; done; fi
echo ALL_DONE
