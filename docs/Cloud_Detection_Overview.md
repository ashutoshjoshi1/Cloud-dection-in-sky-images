# Cloud Detection System — Quick Overview (for Novices)

This document explains **how we plan to build** the cloud detection system in plain language.

---

## What does it do?

The system **finds clouds in sky images**. For each image (from a camera or a file), it:

- Marks which pixels are **cloud** and which are **clear sky**
- Reports a **cloud cover** value (e.g. 15% of the sky is cloudy)

This is useful for **solar forecasting**: clouds reduce solar power, so knowing cloud cover helps predict PV output.

---

## Big picture: three main pieces

| Piece | Role |
|-------|------|
| **1. Sun position** | We compute where the sun is in the image using **time + your location** (no need to “see” the sun in the image). |
| **2. Clear Sky Library (CSL)** | A set of **reference images of clear sky** at different sun positions. We use them to compare “what clear sky looks like” at that same sun position. |
| **3. NRBR + CSL algorithm** | We combine two ideas (see below) to decide, pixel by pixel, whether it’s cloud or clear sky. |

---

## How do we tell “cloud” from “clear sky”?

### Idea 1: Color (Red vs Blue) — NRBR

- **Clear sky** scatters more blue light → looks blue → **high “blue vs red” ratio (NRBR)**.
- **Clouds** scatter blue and red more equally → look white/grey → **low NRBR**.

So: **low NRBR** often means **cloud**.  
Problem: the **area around the sun** is also bright and can look “cloud-like” (low NRBR), so we’d wrongly mark it as cloud if we only used NRBR.

### Idea 2: Compare to “ideal clear sky” — CSL

- We have a **Clear Sky Library**: images of **only clear sky** at many sun positions.
- For each new image, we find the **CSL image with the most similar sun position**.
- We **compare** the new image to that clear-sky reference:  
  **Cloud pixels** will **differ** a lot from the reference; **clear-sky pixels** will **match** it.

So: **large difference from clear-sky reference** → **cloud**.

### Putting it together: NRBR + CSL

- **Mostly clear sky** (low cloud cover): we trust the **CSL comparison** (avoids misclassifying the bright area around the sun).
- **Very cloudy** (high cloud cover): we use **NRBR** (simple “low blue/red ratio = cloud”).
- **In between**: we use **NRBR only outside the sun region**, and CSL elsewhere.

So the “plan” is: **sun position** → **pick best clear-sky reference** → **compare and/or use NRBR** → **cloud mask + cloud cover %**.

---

## What you need to run it

- **Time** (when the image was taken).
- **Location** (latitude, longitude) — so we can compute sun position and time zone.
- **Sky image** (e.g. from a camera), resized to **64×64** for the core algorithm.
- **Clear Sky Library** — pre-loaded reference images and their sun positions (in `sample_data/clear_sky_library/`).

---

## Flow (step by step)

1. **User** enters a place (e.g. “Stanford, CA”) → we get **latitude/longitude**.
2. **Camera** (or image file) gives a **sky image**.
3. We **resize** the image to 64×64 and get **current time**.
4. **Sun position** is computed from time + location → (x, y) in the image + sun mask.
5. We **match** this sun position to the **Clear Sky Library** → one reference “clear sky” image.
6. We compute **NRBR** for the current image and for the reference image, then **difference** (and use NRBR rules as above).
7. We **classify** each pixel → **cloud** or **not** → **cloud mask** (green overlay) and **cloud cover %**.
8. The **GUI** shows: original feed, feed with cloud overlay, and cloud cover.

---

## Summary

- **Goal:** Detect clouds in sky images and estimate cloud cover.
- **Method:** Use **sun position** (from time + location), a **Clear Sky Library**, and a **red/blue ratio (NRBR)** combined so that we get good results in clear, partly cloudy, and very cloudy conditions.
- **No heavy AI:** Simple math and thresholds, no GPU or big neural networks — suitable for real-time use on a laptop.

For more detail and formulas, see the main **README.md** and the papers cited there.
