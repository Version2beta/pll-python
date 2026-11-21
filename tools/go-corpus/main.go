// Complete; do not change. Public API only; all numeric wire values are strings.
package main

import (
	"encoding/json"
	"fmt"
	p "github.com/version2beta/pll"
	"math"
	"os"
	"strconv"
	"time"
)

type Op struct {
	Name string   `json:"name"`
	Args []string `json:"args"`
}
type Case struct {
	ID        string            `json:"id"`
	Kind      string            `json:"kind"`
	Rate      []string          `json:"rate"`
	Config    map[string]string `json:"config"`
	Ops       []Op              `json:"ops"`
	Tolerance string            `json:"tolerance"`
	Rationale string            `json:"rationale"`
}

func i(s string) int64 {
	v, e := strconv.ParseInt(s, 10, 64)
	if e != nil {
		panic(e)
	}
	return v
}
func u(s string) uint64 {
	v, e := strconv.ParseUint(s, 10, 64)
	if e != nil {
		panic(e)
	}
	return v
}
func fl(s string) float64 {
	v, e := strconv.ParseUint(s, 16, 64)
	if e != nil {
		panic(e)
	}
	return math.Float64frombits(v)
}
func dec(v any) string { return fmt.Sprint(v) }
func errcode(e error) []string {
	if e == nil {
		return nil
	}
	switch e {
	case p.ErrInvalidRate:
		return []string{"error", "invalid_rate"}
	case p.ErrInvalidArgument:
		return []string{"error", "invalid_argument"}
	case p.ErrOverflow:
		return []string{"error", "overflow"}
	case p.ErrOrder:
		return []string{"error", "order"}
	case p.ErrNotAnchored:
		return []string{"error", "not_anchored"}
	}
	if c, ok := e.(*p.ConfigError); ok {
		return []string{"error", "config", c.Field, c.Reason}
	}
	panic(e)
}
func run(c Case) [][]string {
	r, e := p.UnitsPerSecond(u(c.Rate[0]), u(c.Rate[1]))
	if c.Kind == "bits" {
		r, e = p.BitsPerSecond(u(c.Rate[0]), u(c.Rate[1]))
	}
	if e != nil {
		return [][]string{errcode(e)}
	}
	out := [][]string{{"rate", dec(r.Num()), dec(r.Den()), r.String()}}
	var pac *p.Pacer
	var f *p.Follower
	spans := []p.Span{}
	if c.Kind == "pacer" {
		pac, e = p.NewPacer(r)
	} else if c.Kind == "follower" {
		cfg := p.DefaultFollowerConfig(r)
		for k, v := range c.Config {
			switch k {
			case "Nominal":
				cfg.Nominal = p.Rate{}
			case "Bandwidth":
				cfg.Bandwidth = fl(v)
			case "Damping":
				cfg.Damping = fl(v)
			case "MaxOffsetPPM":
				cfg.MaxOffsetPPM = fl(v)
			case "Window":
				cfg.Window = time.Duration(i(v))
			case "OutlierThreshold":
				cfg.OutlierThreshold = time.Duration(i(v))
			case "StepAfter":
				cfg.StepAfter = int(i(v))
			case "LockThreshold":
				cfg.LockThreshold = time.Duration(i(v))
			case "LockCount":
				cfg.LockCount = int(i(v))
			case "HoldoverAfter":
				cfg.HoldoverAfter = time.Duration(i(v))
			default:
				panic(k)
			}
		}
		f, e = p.NewFollower(cfg)
	}
	if e != nil {
		return append(out, errcode(e))
	}
	for _, o := range c.Ops {
		a := o.Args
		var v []string
		var e error
		switch o.Name {
		case "claim", "due":
			var s p.Span
			if o.Name == "claim" {
				s, e = pac.Claim(u(a[0]))
			} else {
				s, e = pac.Due(time.Duration(i(a[0])), u(a[1]))
			}
			if e == nil {
				spans = append(spans, s)
				v = []string{"span", dec(s.First), dec(s.Count)}
				if s.Count > 0 {
					v = append(v, dec(int64(s.Time(0))), dec(int64(s.Time(s.Count-1))))
				}
			}
		case "time":
			v = []string{"int", dec(int64(spans[i(a[0])].Time(u(a[1]))))}
		case "all":
			v = []string{"all"}
			n := 0
			for s, t := range spans[i(a[0])].All() {
				v = append(v, dec(s), dec(int64(t)))
				n++
				if n >= int(i(a[1])) {
					break
				}
			}
		case "skip":
			var n uint64
			n, e = pac.Skip(time.Duration(i(a[0])), u(a[1]))
			v = []string{"int", dec(n)}
		case "next_due":
			var s uint64
			var t time.Duration
			s, t, e = pac.NextDue()
			v = []string{"next", dec(s), dec(int64(t))}
		case "set_trim":
			e = pac.SetTrim(i(a[0]))
			v = []string{"ok"}
		case "pacer_trim":
			v = []string{"int", dec(pac.Trim())}
		case "observe":
			var x p.Observation
			x, e = f.Observe(time.Duration(i(a[0])), i(a[1]))
			v = []string{"observation", dec(uint8(x.Status)), dec(int64(x.Error))}
		case "local":
			var x time.Duration
			x, e = f.Local(i(a[0]))
			v = []string{"int", dec(int64(x))}
		case "remote":
			var x int64
			x, e = f.Remote(time.Duration(i(a[0])))
			v = []string{"int", dec(x)}
		case "offset":
			v = []string{"float", fmt.Sprintf("%016x", math.Float64bits(f.Offset()))}
		case "trim":
			v = []string{"int", dec(f.Trim())}
		case "jitter":
			v = []string{"int", dec(int64(f.Jitter()))}
		case "state":
			v = []string{"state", dec(uint8(f.State(time.Duration(i(a[0])))))}
		case "reset":
			f.Reset()
			v = []string{"ok"}
		default:
			panic(o.Name)
		}
		if e != nil {
			v = errcode(e)
		}
		out = append(out, v)
	}
	return out
}
func main() {
	var cases []Case
	if e := json.NewDecoder(os.Stdin).Decode(&cases); e != nil {
		panic(e)
	}
	out := [][][]string{}
	for _, c := range cases {
		out = append(out, run(c))
	}
	enc := json.NewEncoder(os.Stdout)
	enc.SetEscapeHTML(false)
	if e := enc.Encode(out); e != nil {
		panic(e)
	}
}
