package result

import "pappumath/entity"

// Amounts are signed integers in one server-defined money unit. Never mix currencies.
type PappuInput struct {
	Version string
	Bets    entity.Bets // frozen final accepted amounts; undo deltas have already been applied
}

// Outcome is drawn once per room, then reused for every player in that room.
// Only ordinary, single-winning-picture rounds are implemented from current evidence.
type Outcome struct {
	Winner     entity.Area
	ReturnOdds entity.Odds // gross return including stake; 0 means base return 10
	Pic        int32
	IsBonus    bool // true is reserved, and rejected until special-mode rules are established
}

type PappuOutput struct {
	Winner          entity.Area
	BaseReturnOdds  entity.Odds
	FinalReturnOdds entity.Odds
	Pic             int32
	IsBonus         bool
	BetTotal        int64
	TotalWin        int64    // gross return; winning bet * FinalReturnOdds; NEVER add stake again
	NetWin          int64    // TotalWin - BetTotal
	UsedRNG         []uint64 // server audit only; never serialize into client packets
}

type RoomInput struct {
	Version string
	Players []entity.Bets // index remains associated with the server's own player list
}

type RoomOutput struct {
	Outcome Outcome
	Players []PappuOutput
	UsedRNG []uint64 // one draw for the entire room, server audit only
}
