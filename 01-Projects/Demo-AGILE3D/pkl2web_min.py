#!/usr/bin/env python3
# pkl2web_min.py — Convert GT/det PKLs into web-friendly sequence assets
# Usage example:
#   python pkl2web_min.py \
#     --seq-id v_1784_1828 --out ./sequences/v_1784_1828 --fps 10 \
#     --start 1784 --end 1828 \
#     --gt "/data/gt_chunks/*.pkl" \
#     --det DSVT_Voxel="/data/det_dsvt_chunks/*.pkl"
#
# Notes:
# - Assumes PKL chunks are dict-like with arrays/lists per key OR list of per-frame dicts.
# - GT: expects keys including 'frame_id', 'points' ([:,0:3] used), 'gt_boxes' ([:,0:7]).
# - DET: expects 'frame_id', 'boxes_lidar' ([:,0:7]), 'score', 'pred_labels' (or 'name').
# - Writes:
#   frames/<FID>.bin (Float32 XYZ),
#   frames/<FID>.gt.json,
#   frames/<FID>.det.<branch>.json,
#   manifest.json

import argparse, glob, json, os, pickle, sys
from pathlib import Path
from typing import Dict, Iterable, List, Tuple, Any, Optional
import numpy as np

def ensure_dir(p: Path):
    p.mkdir(parents=True, exist_ok=True)

def save_json(path: Path, obj: Any):
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w") as f:
        json.dump(obj, f, separators=(",", ":"), ensure_ascii=False)

def coerce_list(x):
    if x is None: return []
    if isinstance(x, (list, tuple)): return list(x)
    try:
        return list(x)
    except Exception:
        return [x]

def iter_pkl_records(pkl_path: Path) -> Iterable[Dict[str, Any]]:
    with pkl_path.open("rb") as f:
        data = pickle.load(f)
    # Case 1: list of per-frame dicts
    if isinstance(data, list) and (len(data) == 0 or isinstance(data[0], dict)):
        for rec in data:
            yield rec
        return
    # Case 2: dict of lists/arrays, index-aligned by length of 'frame_id'
    if isinstance(data, dict) and "frame_id" in data:
        ids = coerce_list(data["frame_id"])
        n = len(ids)
        # Collect keys with list/array lengths == n
        keys = [k for k, v in data.items() if hasattr(v, "__len__") and len(coerce_list(v)) == n]
        rows = {k: coerce_list(data[k]) for k in keys}
        for i in range(n):
            rec = {k: rows[k][i] for k in keys}
            yield rec
        return
    # Fallback: single record dict
    if isinstance(data, dict):
        yield data
        return
    raise ValueError(f"Unsupported PKL structure in {pkl_path}")

def gather_frames_from_globs(globs: List[str]) -> Iterable[Dict[str, Any]]:
    files = []
    for g in globs:
        files.extend(glob.glob(g))
    for p in sorted(set(files)):
        for rec in iter_pkl_records(Path(p)):
            yield rec

def to_int_frame_id(frame_id: Any) -> Optional[int]:
    try:
        if isinstance(frame_id, (bytes, bytearray)):
            frame_id = frame_id.decode("utf-8", "ignore")
        s = str(frame_id).strip()
        # allow zero-padded strings
        return int(s)
    except Exception:
        return None

def frame_str(fid: int, width: int) -> str:
    return str(fid).zfill(width)

def extract_xyz(points: Any) -> np.ndarray:
    arr = np.asarray(points)
    if arr.ndim != 2 or arr.shape[1] < 3:
        raise ValueError(f"points has shape {arr.shape}, expected (N,>=3)")
    return arr[:, :3].astype(np.float32, copy=False)

def extract_boxes7(x: Any) -> np.ndarray:
    arr = np.asarray(x)

    # If shape is (1, M, N), squeeze it to (M, N)
    if arr.ndim == 3 and arr.shape[0] == 1:
        arr = arr.squeeze(0)

    if arr.ndim != 2 or arr.shape[1] < 7:
        raise ValueError(f"boxes has shape {arr.shape}, expected (M,7)")
    return arr[:, :7]

def safe_list(a) -> List:
    try:
        return list(a)
    except Exception:
        return []

def build_det_objs(boxes7: np.ndarray, scores: Optional[Any], labels: Optional[Any]) -> List[Dict[str, Any]]:
    sc = np.asarray(scores) if scores is not None else None
    lb = np.asarray(labels) if labels is not None else None
    out = []
    for i in range(boxes7.shape[0]):
        o = {
            "x": float(boxes7[i,0]), "y": float(boxes7[i,1]), "z": float(boxes7[i,2]),
            "dx": float(boxes7[i,3]), "dy": float(boxes7[i,4]), "dz": float(boxes7[i,5]),
            "heading": float(boxes7[i,6]),
        }
        if sc is not None and i < sc.shape[0]:
            o["score"] = float(sc[i])
        if lb is not None and i < lb.shape[0]:
            # keep numeric; app can map via classMap
            try:
                o["label"] = int(lb[i])
            except Exception:
                o["label"] = str(lb[i])
        out.append(o)
    return out

def build_gt_objs(boxes7: np.ndarray, labels: Optional[Any]) -> List[Dict[str, Any]]:
    lb = np.asarray(labels) if labels is not None else None
    out = []
    for i in range(boxes7.shape[0]):
        o = {
            "x": float(boxes7[i,0]), "y": float(boxes7[i,1]), "z": float(boxes7[i,2]),
            "dx": float(boxes7[i,3]), "dy": float(boxes7[i,4]), "dz": float(boxes7[i,5]),
            "heading": float(boxes7[i,6]),
        }
        if lb is not None and i < lb.shape[0]:
            try:
                o["label"] = int(lb[i])
            except Exception:
                o["label"] = str(lb[i])
        out.append(o)
    return out

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--seq-id", required=True)
    ap.add_argument("--out", required=True, help="output dir for this sequence (will create)")
    ap.add_argument("--fps", type=int, default=10)
    ap.add_argument("--start-idx", type=int, default=0, help="start ordinal index (0-based) within concatenated GT records")
    ap.add_argument("--end-idx", type=int, help="end ordinal index (0-based, inclusive)")
    ap.add_argument("--limit", type=int, help="optional max number of frames to emit (from start-idx)")
    ap.add_argument("--gt", action="append", default=[], help="glob for GT PKL(s); repeatable")
    ap.add_argument("--det", action="append", default=[], help="branchId=glob for DET PKL(s); repeatable")
    args = ap.parse_args()

    seq_id = args.seq_id
    out_dir = Path(args.out)
    frames_dir = out_dir / "frames"
    ensure_dir(frames_dir)

    # Index detections per branch → {branch: {fid: [boxObjs...]}}
    det_index: Dict[str, Dict[str, List[Dict[str, Any]]]] = {}
    branches: List[str] = []

    for det_arg in args.det:
        if "=" not in det_arg:
            print(f"--det expects branch=glob, got {det_arg}", file=sys.stderr)
            sys.exit(2)
        branch, pattern = det_arg.split("=", 1)
        branches.append(branch)
        det_index[branch] = {}
        for rec in gather_frames_from_globs([pattern]):
            fid_str = str(rec.get("frame_id"))
            if not fid_str:
                continue
            boxes = rec.get("boxes_lidar")
            scores = rec.get("score")
            labels = rec.get("pred_labels")
            if labels is None:
                labels = rec.get("name")
            if boxes is None:
                det_index[branch].setdefault(fid_str, [])
                continue
            b7 = extract_boxes7(boxes)
            det_index[branch].setdefault(fid_str, []).extend(build_det_objs(b7, scores, labels))

    # Pass 1: identify available GT frames and write per-frame artifacts
    selected_ids: List[str] = []
    gt_globs = args.gt if args.gt else []

    start_idx = max(0, int(args.start_idx or 0))
    end_idx = int(args.end_idx) if args.end_idx is not None else None
    limit = int(args.limit) if args.limit is not None else None

    idx = -1
    seq_counter = 0
    PAD = 6  # filename zero-pad width

    for rec in gather_frames_from_globs(gt_globs):
        fid_str = str(rec.get("frame_id"))
        if not fid_str:
            continue
        idx += 1
        if idx < start_idx:
            continue
        if end_idx is not None and idx > end_idx:
            break
        if limit is not None and seq_counter >= limit:
            break

        fname = str(seq_counter).zfill(PAD)

        # Points .bin (XYZ only)
        pts = rec.get("points")
        if pts is not None:
            pts_xyz = extract_xyz(pts)
            (frames_dir / f"{fname}.bin").write_bytes(pts_xyz.tobytes(order="C"))

        # GT .json (boxes7)
        gt_boxes = rec.get("gt_boxes")
        gt_labels = rec.get("gt_names") or rec.get("gt_labels") or None
        if gt_boxes is not None:
            b7 = extract_boxes7(gt_boxes)
            save_json(frames_dir / f"{fname}.gt.json", {"boxes": build_gt_objs(b7, gt_labels)})

        # DET per-branch .json (if present for this fid)
        for branch in branches:
            boxes = det_index.get(branch, {}).get(fid_str)
            if boxes is not None:
                save_json(frames_dir / f"{fname}.det.{branch}.json", {"boxes": boxes})

        selected_ids.append(fid_str)
        seq_counter += 1

    if not selected_ids:
        print("No frames written (check --gt globs and index filters)", file=sys.stderr)
        sys.exit(1)

    # Emit manifest.json
    frames_manifest = []
    for i, orig_id in enumerate(selected_ids):
        pad = str(i).zfill(PAD)
        entry = {
            "id": pad,
            "origId": orig_id,
            "urls": {
                "points": f"frames/{pad}.bin"
            }
        }
        if (frames_dir / f"{pad}.gt.json").exists():
            entry["urls"]["gt"] = f"frames/{pad}.gt.json"
        det_urls = {}
        for branch in branches:
            if (frames_dir / f"{pad}.det.{branch}.json").exists():
                det_urls[branch] = f"frames/{pad}.det.{branch}.json"
        if det_urls:
            entry["urls"]["det"] = det_urls
        try:
            pc = os.path.getsize(frames_dir / f"{pad}.bin") // (4*3)
            entry["pointCount"] = int(pc)
        except Exception:
            pass
        frames_manifest.append(entry)

    manifest = {
        "version": "1.0",
        "sequenceId": seq_id,
        "fps": int(args.fps),
        "branches": branches,
        "frames": frames_manifest
    }
    save_json(out_dir / "manifest.json", manifest)
    print(f"Wrote sequence to: {out_dir}")
    print(f"Frames: {len(frames_manifest)}")

if __name__ == "__main__":
    main()