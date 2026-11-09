package entity

// Area is the original Pappu type, 1..12. Arrays use screen index Area-1.
type Area int

const AreaCount = 12

// Explicit values prevent any dependency on UI component traversal order.
const (
	AreaUmbrella    Area = 1
	AreaSoccer      Area = 2
	AreaSun         Area = 3
	AreaDiya        Area = 4
	AreaBull        Area = 5
	AreaBucket      Area = 6
	AreaKite        Area = 7
	AreaWhippingTop Area = 8
	AreaRose        Area = 9
	AreaButterfly   Area = 10
	AreaPigeon      Area = 11
	AreaRabbit      Area = 12
)

const BaseNetOdds int64 = 9
const BaseReturnOdds int64 = BaseNetOdds + 1

type Bets [AreaCount]int64
type Odds [AreaCount]int64

func (a Area) Valid() bool { return a >= AreaUmbrella && a <= AreaRabbit }
func (a Area) Index() int  { return int(a) - 1 }

// AreaNames returns a value copy in screen row-major order, never column traversal order.
func AreaNames() [AreaCount]string {
	return [AreaCount]string{"Umbrella", "Soccer", "Sun", "Diya", "Bull", "Bucket", "Kite", "WhippingTop", "Rose", "Butterfly", "Pigeon", "Rabbit"}
}
