# LMU / rFactor 2 Telemetry Format Reference

> **Purpose:** Reference spec for parsing Le Mans Ultimate telemetry data.
> LMU is built on the rFactor 2 engine and uses the same shared memory plugin.

---

## Architecture

```
LMU (sim process)
    │
    ├─── Shared Memory Buffers ───► Electron Client (reads via native addon)
    │                                     │
    │                                     │ POST /telemetry (JSON)
    │                                     ▼
    │                              LMU Telemetry API (this project)
    │
    └─── UDP Broadcast (optional) ──► External tools
```

**Primary data path:** The Electron client spawns `scripts/lmu_capture_bridge.py`. **Manual** mode uses `session_id` on `POST /telemetry`. **Automatic** mode (bridge `--auto`, default in the Live capture UI) also reads **`$rFactor2SMMP_Scoring$`** and sends `track_name`, `car_name`, `driver_name`, and `session_type` so the API can `get_or_create_session` without a fixed id. The binary parser in `src/core/parser.py` is used by that bridge and for offline replay of captured memory dumps.

---

## Shared Memory Buffers

LMU exposes telemetry via Windows shared memory mapped files, provided by the
[rF2 Shared Memory Map Plugin](https://github.com/TheIronWolfModding/rF2SharedMemoryMapPlugin).

| Buffer Name | Update Rate | Contents |
|---|---|---|
| `$rFactor2SMMP_Telemetry$` | ~50 Hz (every ~20 ms) | Vehicle dynamics, driver inputs, tire data |
| `$rFactor2SMMP_Scoring$` | 1-5 Hz | Lap times, positions, session state, game phase |
| `$rFactor2SMMP_ForceFeedback$` | ~400 Hz | Force feedback magnitude |
| `$rFactor2SMMP_Graphics$` | ~1 Hz | Camera info, display state |
| `$rFactor2SMMP_Extended$` | Varies | Plugin-specific extended data (track rules, etc.) |
| `$rFactor2SMMP_Weather$` | Low freq | Weather conditions, ambient/track temps |

**For this API, we primarily consume data from `Telemetry` and `Scoring` buffers.**

---

## Field Reference — Telemetry Buffer

Source: `rF2VehicleTelemetry` struct (C++) / `rF2VehicleTelemetry` ctypes (Python).

### Driver Inputs

| rF2 Field | Type | Range | Our Field | Conversion |
|---|---|---|---|---|
| `mUnfilteredThrottle` | `c_double` | 0.0 - 1.0 | `throttle` | Direct |
| `mUnfilteredBrake` | `c_double` | 0.0 - 1.0 | `brake` | Direct |
| `mUnfilteredSteering` | `c_double` | -1.0 to 1.0 | `steering` | Direct |
| `mGear` | `c_int` | -1 (R), 0 (N), 1+ | `gear` | Direct |

### Vehicle Dynamics

| rF2 Field | Type | Unit | Our Field | Conversion |
|---|---|---|---|---|
| `mSpeed` | `c_double` | m/s | `speed` | Multiply by 3.6 → km/h |
| `mEngineRPM` | `c_double` | RPM | `rpm` | Direct |
| `mPos.x` | `c_double` | meters | `position_x` | Direct |
| `mPos.y` | `c_double` | meters | `position_y` | Direct (vertical) |
| `mPos.z` | `c_double` | meters | `position_z` | Direct |
| `mLocalVel.x/y/z` | `c_double` | m/s | — | Not stored (future use) |
| `mLocalAccel.x/y/z` | `c_double` | m/s^2 | — | Not stored (future use) |

### Tire Data

Each vehicle has 4 wheels indexed as: `[0]=FL, [1]=FR, [2]=RL, [3]=RR`.

| rF2 Field | Type | Unit | Our Field | Conversion |
|---|---|---|---|---|
| `mWheels[i].mTemperature[0]` | `c_double` | Kelvin | — | Inner temp (not stored individually) |
| `mWheels[i].mTemperature[1]` | `c_double` | Kelvin | `tire_temps` | Subtract 273.15 → Celsius |
| `mWheels[i].mTemperature[2]` | `c_double` | Kelvin | — | Outer temp (not stored individually) |
| `mWheels[i].mPressure` | `c_double` | kPa | `tire_pressures` | Direct |
| `mWheels[i].mWear` | `c_double` | 0.0 - 1.0 | — | Not stored (future use) |
| `mWheels[i].mBrakeTemp` | `c_double` | Celsius | — | Not stored (future use) |
| `mWheels[i].mTireLoad` | `c_double` | Newtons | — | Not stored (future use) |

**Note:** We store the middle temperature (`mTemperature[1]`) as the representative
tire temperature. Inner/outer temps can be added later if needed.

**Tire data is stored as a `TireData` object:**
```json
{
  "front_left": 95.2,
  "front_right": 96.1,
  "rear_left": 98.0,
  "rear_right": 97.5
}
```

### Fuel

| rF2 Field | Type | Unit | Our Field | Conversion |
|---|---|---|---|---|
| `mFuel` | `c_double` | liters | `fuel_level` | Direct |
| `mFuelCapacity` | `c_double` | liters | — | Not stored (future use) |

### Timing

| rF2 Field | Type | Unit | Our Field | Conversion |
|---|---|---|---|---|
| `mElapsedTime` | `c_double` | seconds | `timestamp` | Convert to datetime (session start + elapsed) |
| `mLapStartET` | `c_double` | seconds | — | Used for lap time calculation |
| `mDeltaTime` | `c_double` | seconds | — | Time since last telemetry update |
| `mLapNumber` | `c_int` | — | `lap_number` | Direct |

---

## Field Reference — Scoring Buffer

Source: `rF2ScoringInfo` and `rF2VehicleScoring` structs.

### Session Info

| rF2 Field | Type | Values | Purpose |
|---|---|---|---|
| `mGamePhase` | `c_int` | 0=Before session, 1=Reconnaissance, 2=Grid, 3=Formation, 4=Countdown, 5=Green flag, 6=Full course yellow, 7=Session stopped, 8=Session over | Detect session state transitions |
| `mSession` | `c_int` | 0=Test day, 1-4=Practice 1-4, 5-8=Qual 1-4, 9-13=Warmup/Race | Map to our `SessionType` enum |

### Session Type Mapping

| `mSession` Value | Our `SessionType` |
|---|---|
| 0 (Test day) | `PRACTICE` |
| 1-4 (Practice) | `PRACTICE` |
| 5-8 (Qualifying) | `QUALIFYING` |
| 9 (Warmup) | `PRACTICE` |
| 10-13 (Race) | `RACE` |

### Per-Vehicle Scoring

| rF2 Field | Type | Purpose |
|---|---|---|
| `mVehicleName` | `c_char[64]` | Car model name → `car_name` |
| `mTrackName` | `c_char[64]` | Track name → `track_name` |
| `mDriverName` | `c_char[32]` | Driver name → `driver_name` |
| `mBestLapTime` | `c_double` | Best lap time in seconds → `best_lap_time` |
| `mLastLapTime` | `c_double` | Last completed lap time |
| `mTotalLaps` | `c_int` | Total laps completed → `total_laps` |
| `mSector` | `c_int` | Current sector (0, 1, 2) → `sector` |
| `mInPits` | `c_int` | 0=on track, 1=in pits |
| `mPlace` | `c_int` | Current position |

---

## Weather Data

| rF2 Field | Type | Unit | Our Field |
|---|---|---|---|
| `mAmbientTemp` | `c_double` | Celsius | `weather_conditions` (as part of string) |
| `mTrackTemp` | `c_double` | Celsius | `weather_conditions` |
| `mRaining` | `c_double` | 0.0 - 1.0 | `weather_conditions` → "dry" / "wet" / "mixed" |

**Weather mapping logic:**
- `mRaining` < 0.1 → `"dry"`
- `mRaining` >= 0.1 and < 0.5 → `"mixed"`
- `mRaining` >= 0.5 → `"wet"`

---

## Binary Layout Overview

The shared memory buffers use a versioned double-buffering scheme:

```
Buffer Header:
  mVersionUpdateBegin  (c_int)     ← Incremented before update
  mVersionUpdateEnd    (c_int)     ← Incremented after update
  mBytesUpdatedHint    (c_int)     ← How many bytes changed

  (When Begin != End, the buffer is mid-update — skip this read)

Telemetry Buffer Body:
  mNumVehicles         (c_int)
  mVehicles[64]        (rF2VehicleTelemetry[64])   ← Up to 64 vehicles
```

Each `rF2VehicleTelemetry` struct is approximately **1800 bytes** (exact size depends
on plugin version). The total telemetry buffer is ~115 KB.

---

## Upstream References

- [rF2SharedMemoryMapPlugin (C++ source)](https://github.com/TheIronWolfModding/rF2SharedMemoryMapPlugin)
- [rF2SharedMemoryMap.hpp (struct definitions)](https://github.com/TheIronWolfModding/rF2SharedMemoryMapPlugin/blob/master/Include/rFactor2SharedMemoryMap.hpp)
- [pyRfactor2SharedMemory (Python ctypes)](https://github.com/TonyWhitley/pyRfactor2SharedMemory)
- [rF2data.py (Python field definitions)](https://github.com/TonyWhitley/pyRfactor2SharedMemory/blob/master/rF2data.py)
- [TinyPedal (LMU overlay using pyRfactor2SharedMemory)](https://github.com/TinyPedal/TinyPedal)
