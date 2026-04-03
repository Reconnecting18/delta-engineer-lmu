"""ctypes layouts for rF2/LMU scoring shared memory (Windows).

Aligned with The Iron Wolf's rF2State.h / pyRfactor2SharedMemory rF2data.py
(Pack=4, MAX_MAPPED_VEHICLES=128). Used for automatic session context from
``$rFactor2SMMP_Scoring$``.

References:
- https://github.com/TheIronWolfModding/rF2SharedMemoryMapPlugin
- https://github.com/TonyWhitley/pyRfactor2SharedMemory
"""

from __future__ import annotations

import ctypes

MAX_MAPPED_VEHICLES = 128


class rF2Vec3(ctypes.Structure):
    _pack_ = 4
    _fields_ = [
        ("x", ctypes.c_double),
        ("y", ctypes.c_double),
        ("z", ctypes.c_double),
    ]


class rF2ScoringInfo(ctypes.Structure):
    _pack_ = 4
    _fields_ = [
        ("mTrackName", ctypes.c_ubyte * 64),
        ("mSession", ctypes.c_int),
        ("mCurrentET", ctypes.c_double),
        ("mEndET", ctypes.c_double),
        ("mMaxLaps", ctypes.c_int),
        ("mLapDist", ctypes.c_double),
        ("pointer1", ctypes.c_ubyte * 8),
        ("mNumVehicles", ctypes.c_int),
        ("mGamePhase", ctypes.c_ubyte),
        ("mYellowFlagState", ctypes.c_ubyte),
        ("mSectorFlag", ctypes.c_ubyte * 3),
        ("mStartLight", ctypes.c_ubyte),
        ("mNumRedLights", ctypes.c_ubyte),
        ("mInRealtime", ctypes.c_ubyte),
        ("mPlayerName", ctypes.c_ubyte * 32),
        ("mPlrFileName", ctypes.c_ubyte * 64),
        ("mDarkCloud", ctypes.c_double),
        ("mRaining", ctypes.c_double),
        ("mAmbientTemp", ctypes.c_double),
        ("mTrackTemp", ctypes.c_double),
        ("mWind", rF2Vec3),
        ("mMinPathWetness", ctypes.c_double),
        ("mMaxPathWetness", ctypes.c_double),
        ("mGameMode", ctypes.c_ubyte),
        ("mIsPasswordProtected", ctypes.c_ubyte),
        ("mServerPort", ctypes.c_short),
        ("mServerPublicIP", ctypes.c_int),
        ("mMaxPlayers", ctypes.c_int),
        ("mServerName", ctypes.c_ubyte * 32),
        ("mStartET", ctypes.c_float),
        ("mAvgPathWetness", ctypes.c_double),
        ("mExpansion", ctypes.c_ubyte * 200),
        ("pointer2", ctypes.c_ubyte * 8),
    ]


class rF2VehicleScoring(ctypes.Structure):
    _pack_ = 4
    _fields_ = [
        ("mID", ctypes.c_int),
        ("mDriverName", ctypes.c_ubyte * 32),
        ("mVehicleName", ctypes.c_ubyte * 64),
        ("mTotalLaps", ctypes.c_short),
        ("mSector", ctypes.c_ubyte),
        ("mFinishStatus", ctypes.c_ubyte),
        ("mLapDist", ctypes.c_double),
        ("mPathLateral", ctypes.c_double),
        ("mTrackEdge", ctypes.c_double),
        ("mBestSector1", ctypes.c_double),
        ("mBestSector2", ctypes.c_double),
        ("mBestLapTime", ctypes.c_double),
        ("mLastSector1", ctypes.c_double),
        ("mLastSector2", ctypes.c_double),
        ("mLastLapTime", ctypes.c_double),
        ("mCurSector1", ctypes.c_double),
        ("mCurSector2", ctypes.c_double),
        ("mNumPitstops", ctypes.c_short),
        ("mNumPenalties", ctypes.c_short),
        ("mIsPlayer", ctypes.c_ubyte),
        ("mControl", ctypes.c_ubyte),
        ("mInPits", ctypes.c_ubyte),
        ("mPlace", ctypes.c_ubyte),
        ("mVehicleClass", ctypes.c_ubyte * 32),
        ("mTimeBehindNext", ctypes.c_double),
        ("mLapsBehindNext", ctypes.c_int),
        ("mTimeBehindLeader", ctypes.c_double),
        ("mLapsBehindLeader", ctypes.c_int),
        ("mLapStartET", ctypes.c_double),
        ("mPos", rF2Vec3),
        ("mLocalVel", rF2Vec3),
        ("mLocalAccel", rF2Vec3),
        ("mOri", rF2Vec3 * 3),
        ("mLocalRot", rF2Vec3),
        ("mLocalRotAccel", rF2Vec3),
        ("mHeadlights", ctypes.c_ubyte),
        ("mPitState", ctypes.c_ubyte),
        ("mServerScored", ctypes.c_ubyte),
        ("mIndividualPhase", ctypes.c_ubyte),
        ("mQualification", ctypes.c_int),
        ("mTimeIntoLap", ctypes.c_double),
        ("mEstimatedLapTime", ctypes.c_double),
        ("mPitGroup", ctypes.c_ubyte * 24),
        ("mFlag", ctypes.c_ubyte),
        ("mUnderYellow", ctypes.c_ubyte),
        ("mCountLapFlag", ctypes.c_ubyte),
        ("mInGarageStall", ctypes.c_ubyte),
        ("mUpgradePack", ctypes.c_ubyte * 16),
        ("mPitLapDist", ctypes.c_float),
        ("mBestLapSector1", ctypes.c_float),
        ("mBestLapSector2", ctypes.c_float),
        ("mExpansion", ctypes.c_ubyte * 48),
    ]


class rF2Scoring(ctypes.Structure):
    """Full scoring mapped buffer (version block + body), matching pyRfactor2 layout."""

    _pack_ = 4
    _fields_ = [
        ("mVersionUpdateBegin", ctypes.c_int),
        ("mVersionUpdateEnd", ctypes.c_int),
        ("mBytesUpdatedHint", ctypes.c_int),
        ("mScoringInfo", rF2ScoringInfo),
        ("mVehicles", rF2VehicleScoring * MAX_MAPPED_VEHICLES),
    ]


RF2_SCORING_BUFFER_BYTES = ctypes.sizeof(rF2Scoring)
