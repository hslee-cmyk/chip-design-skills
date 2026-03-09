# Verilog-A Common Circuit Models

## 1. Basic Passive Components

### Resistor

```verilog-a
`include "disciplines.vams"

module resistor(p, n);
    inout p, n;
    electrical p, n;

    parameter real r = 1k from (0:inf);

    analog V(p, n) <+ r * I(p, n);
endmodule
```

### Capacitor

```verilog-a
module capacitor(p, n);
    inout p, n;
    electrical p, n;

    parameter real c = 1p from (0:inf);
    parameter real ic = 0;  // initial voltage

    analog begin
        @(initial_step)
            V(p, n) <+ ic;
        I(p, n) <+ c * ddt(V(p, n));
    end
endmodule
```

### Inductor

```verilog-a
module inductor(p, n);
    inout p, n;
    electrical p, n;

    parameter real l = 1n from (0:inf);
    parameter real ic = 0;  // initial current

    analog begin
        V(p, n) <+ l * ddt(I(p, n));
        @(initial_step)
            I(p, n) <+ ic;
    end
endmodule
```

---

## 2. Voltage and Current Sources

### DC Voltage Source

```verilog-a
module vsource_dc(p, n);
    inout p, n;
    electrical p, n;

    parameter real vdc = 1.0;

    analog V(p, n) <+ vdc;
endmodule
```

### DC Current Source

```verilog-a
module isource_dc(p, n);
    inout p, n;
    electrical p, n;

    parameter real idc = 1m;

    analog I(p, n) <+ idc;
endmodule
```

### Sinusoidal Voltage Source

```verilog-a
module vsource_sin(p, n);
    inout p, n;
    electrical p, n;

    parameter real vdc = 0;
    parameter real vamp = 1.0;
    parameter real freq = 1M;
    parameter real phase = 0;  // degrees

    analog begin
        V(p, n) <+ vdc + vamp * sin(2 * `M_PI * freq * $abstime + phase * `M_PI / 180);
    end
endmodule
```

### Pulse Voltage Source

```verilog-a
module vsource_pulse(p, n);
    inout p, n;
    electrical p, n;

    parameter real v1 = 0;
    parameter real v2 = 1.0;
    parameter real td = 0;      // delay
    parameter real tr = 1n;     // rise time
    parameter real tf = 1n;     // fall time
    parameter real pw = 10n;    // pulse width
    parameter real per = 100n;  // period

    real t_rel, v_out;

    analog begin
        t_rel = ($abstime - td) % per;

        if ($abstime < td)
            v_out = v1;
        else if (t_rel < tr)
            v_out = v1 + (v2 - v1) * t_rel / tr;
        else if (t_rel < tr + pw)
            v_out = v2;
        else if (t_rel < tr + pw + tf)
            v_out = v2 - (v2 - v1) * (t_rel - tr - pw) / tf;
        else
            v_out = v1;

        V(p, n) <+ v_out;
    end
endmodule
```

---

## 3. Controlled Sources

### VCVS (Voltage Controlled Voltage Source)

```verilog-a
module vcvs(inp, inn, outp, outn);
    input inp, inn;
    output outp, outn;
    electrical inp, inn, outp, outn;

    parameter real gain = 1.0;

    analog V(outp, outn) <+ gain * V(inp, inn);
endmodule
```

### VCCS (Voltage Controlled Current Source)

```verilog-a
module vccs(inp, inn, outp, outn);
    input inp, inn;
    output outp, outn;
    electrical inp, inn, outp, outn;

    parameter real gm = 1m;  // transconductance

    analog I(outp, outn) <+ gm * V(inp, inn);
endmodule
```

### CCVS (Current Controlled Voltage Source)

```verilog-a
module ccvs(inp, inn, outp, outn);
    input inp, inn;
    output outp, outn;
    electrical inp, inn, outp, outn;

    parameter real rm = 1k;  // transresistance

    analog begin
        V(inp, inn) <+ 0;  // zero impedance sense
        V(outp, outn) <+ rm * I(inp, inn);
    end
endmodule
```

### CCCS (Current Controlled Current Source)

```verilog-a
module cccs(inp, inn, outp, outn);
    input inp, inn;
    output outp, outn;
    electrical inp, inn, outp, outn;

    parameter real gain = 1.0;

    analog begin
        V(inp, inn) <+ 0;  // zero impedance sense
        I(outp, outn) <+ gain * I(inp, inn);
    end
endmodule
```

---

## 4. Semiconductor Devices

### Ideal Diode

```verilog-a
module diode_ideal(anode, cathode);
    inout anode, cathode;
    electrical anode, cathode;

    parameter real Is = 1e-14;
    parameter real n = 1.0;  // ideality factor

    analog begin
        I(anode, cathode) <+ Is * (limexp(V(anode, cathode) / (n * $vt)) - 1);
    end
endmodule
```

### Diode with Series Resistance

```verilog-a
module diode_rs(anode, cathode);
    inout anode, cathode;
    electrical anode, cathode, internal;

    parameter real Is = 1e-14;
    parameter real n = 1.0;
    parameter real Rs = 10;

    analog begin
        // Diode equation
        I(anode, internal) <+ Is * (limexp(V(anode, internal) / (n * $vt)) - 1);
        // Series resistance
        V(internal, cathode) <+ Rs * I(internal, cathode);
    end
endmodule
```

### Simple NMOS (Level 1)

```verilog-a
module nmos_simple(d, g, s, b);
    inout d, g, s, b;
    electrical d, g, s, b;

    parameter real vth0 = 0.5;
    parameter real kp = 100u;
    parameter real lambda = 0.01;
    parameter real W = 1u;
    parameter real L = 100n;

    real vgs, vds, vth, ids, beta;

    analog begin
        vgs = V(g, s);
        vds = V(d, s);
        vth = vth0;
        beta = kp * W / L;

        if (vgs <= vth) begin
            // Cutoff
            ids = 0;
        end else if (vds < vgs - vth) begin
            // Linear (triode)
            ids = beta * ((vgs - vth) * vds - 0.5 * vds * vds) * (1 + lambda * vds);
        end else begin
            // Saturation
            ids = 0.5 * beta * pow(vgs - vth, 2) * (1 + lambda * vds);
        end

        I(d, s) <+ ids;
    end
endmodule
```

---

## 5. Switches and MUX

### Ideal Switch

```verilog-a
module switch_ideal(ctrl, p, n);
    input ctrl;
    inout p, n;
    electrical ctrl, p, n;

    parameter real Ron = 1;
    parameter real Roff = 1G;
    parameter real vth = 0.5;
    parameter real tr = 1n;

    real G;

    analog begin
        G = transition(V(ctrl) > vth ? 1/Ron : 1/Roff, 0, tr);
        I(p, n) <+ V(p, n) * G;
    end
endmodule
```

### Analog MUX (2:1)

```verilog-a
module analog_mux_2to1(SEL, IN0, IN1, OUT);
    input SEL;
    logic SEL;
    inout IN0, IN1, OUT;
    electrical IN0, IN1, OUT;

    parameter real Tr = 1n;
    parameter real Ron = 100;
    parameter real Roff = 1G;

    analog begin
        // Conductance-based switching
        I(IN0, OUT) <+ V(IN0, OUT) *
            transition((SEL === 0) ? 1/Ron : 1/Roff, 0, Tr);
        I(IN1, OUT) <+ V(IN1, OUT) *
            transition((SEL === 1) ? 1/Ron : 1/Roff, 0, Tr);
    end
endmodule
```

### Analog MUX (4:1)

```verilog-a
module analog_mux_4to1(SEL, IN0, IN1, IN2, IN3, OUT);
    input [1:0] SEL;
    logic [1:0] SEL;
    inout IN0, IN1, IN2, IN3, OUT;
    electrical IN0, IN1, IN2, IN3, OUT;

    parameter real Tr = 1n;
    parameter real Ron = 100;
    parameter real Roff = 1G;

    analog begin
        I(IN0, OUT) <+ V(IN0, OUT) *
            transition((SEL === 2'b00) ? 1/Ron : 1/Roff, 0, Tr);
        I(IN1, OUT) <+ V(IN1, OUT) *
            transition((SEL === 2'b01) ? 1/Ron : 1/Roff, 0, Tr);
        I(IN2, OUT) <+ V(IN2, OUT) *
            transition((SEL === 2'b10) ? 1/Ron : 1/Roff, 0, Tr);
        I(IN3, OUT) <+ V(IN3, OUT) *
            transition((SEL === 2'b11) ? 1/Ron : 1/Roff, 0, Tr);
    end
endmodule
```

---

## 6. Amplifiers

### Ideal Op-Amp

```verilog-a
module opamp_ideal(inp, inn, out);
    input inp, inn;
    output out;
    electrical inp, inn, out;

    parameter real gain = 1e6;

    analog begin
        V(out) <+ gain * V(inp, inn);
    end
endmodule
```

### Op-Amp with Finite Bandwidth

```verilog-a
module opamp_1pole(inp, inn, out);
    input inp, inn;
    output out;
    electrical inp, inn, out;

    parameter real Adc = 100k;    // DC gain
    parameter real fp = 10;       // dominant pole (Hz)

    analog begin
        V(out) <+ laplace_nd(Adc * V(inp, inn),
                             {1},
                             {1, 1/(2*`M_PI*fp)});
    end
endmodule
```

### Op-Amp with Saturation and Slew Rate

```verilog-a
module opamp_realistic(inp, inn, out, vdd, vss);
    input inp, inn, vdd, vss;
    output out;
    electrical inp, inn, out, vdd, vss;

    parameter real Adc = 100k;
    parameter real gbw = 10M;
    parameter real sr = 1e6;      // slew rate (V/s)
    parameter real rin = 1G;
    parameter real rout = 100;
    parameter real vos = 0;       // input offset

    real vout_int, vout_sat;

    analog begin
        // Input impedance
        I(inp, inn) <+ V(inp, inn) / rin;

        // Gain with single-pole response
        vout_int = laplace_nd(Adc * (V(inp, inn) - vos),
                              {1},
                              {1, 1/(2*`M_PI*gbw/Adc)});

        // Output saturation (smooth tanh)
        vout_sat = 0.5 * (V(vdd) + V(vss)) +
                   0.5 * (V(vdd) - V(vss)) *
                   tanh(4 * (vout_int - 0.5*(V(vdd)+V(vss))) / (V(vdd) - V(vss)));

        // Slew rate limiting
        V(out) <+ slew(vout_sat, sr, -sr);

        // Output impedance (optional)
        // V(out) <+ rout * I(out);
    end
endmodule
```

---

## 7. Comparators

### Simple Comparator

```verilog-a
module comparator(inp, inn, out, vdd, vss);
    input inp, inn, vdd, vss;
    output out;
    electrical inp, inn, out, vdd, vss;

    parameter real tr = 1n;

    real state;

    analog begin
        @(cross(V(inp, inn), 0))
            ;

        if (V(inp, inn) > 0)
            state = V(vdd);
        else
            state = V(vss);

        V(out) <+ transition(state, 0, tr, tr);
    end
endmodule
```

### Comparator with Hysteresis

```verilog-a
module comparator_hyst(inp, inn, out, vdd, vss);
    input inp, inn, vdd, vss;
    output out;
    electrical inp, inn, out, vdd, vss;

    parameter real vhyst = 10m;
    parameter real tr = 1n;

    real state;

    analog begin
        @(initial_step)
            state = (V(inp, inn) > 0) ? 1 : 0;

        if (V(inp, inn) > vhyst/2)
            state = 1;
        else if (V(inp, inn) < -vhyst/2)
            state = 0;

        V(out) <+ transition(state ? V(vdd) : V(vss), 0, tr, tr);
    end
endmodule
```

---

## 8. Data Converters

### Ideal N-bit DAC

```verilog-a
module dac_ideal(din, vref, out);
    input [N-1:0] din;
    input vref;
    output out;
    electrical din[N-1:0], vref, out;

    parameter integer N = 8;
    parameter real tr = 1n;

    integer i;
    real code, vout;

    analog begin
        code = 0;
        for (i = 0; i < N; i = i + 1) begin
            if (V(din[i]) > 0.5)
                code = code + pow(2, i);
        end

        vout = V(vref) * code / pow(2, N);
        V(out) <+ transition(vout, 0, tr);
    end
endmodule
```

### Ideal N-bit ADC (Flash-style)

```verilog-a
module adc_ideal(vin, vref, clk, dout);
    input vin, vref, clk;
    output [N-1:0] dout;
    electrical vin, vref, clk;
    electrical dout[N-1:0];

    parameter integer N = 8;
    parameter real vth_clk = 0.5;
    parameter real tr = 1n;

    integer code, i;
    real lsb;

    analog begin
        @(cross(V(clk) - vth_clk, +1)) begin
            lsb = V(vref) / pow(2, N);
            code = floor(V(vin) / lsb + 0.5);

            if (code < 0) code = 0;
            if (code > pow(2, N) - 1) code = pow(2, N) - 1;
        end

        for (i = 0; i < N; i = i + 1) begin
            V(dout[i]) <+ transition(((code >> i) & 1) ? 1.0 : 0.0, 0, tr);
        end
    end
endmodule
```

---

## 9. Filters

### First-Order Low-Pass Filter

```verilog-a
module lpf_1st(in, out);
    input in;
    output out;
    electrical in, out;

    parameter real fc = 1M;  // cutoff frequency

    analog begin
        V(out) <+ laplace_nd(V(in), {1}, {1, 1/(2*`M_PI*fc)});
    end
endmodule
```

### Second-Order Low-Pass Filter

```verilog-a
module lpf_2nd(in, out);
    input in;
    output out;
    electrical in, out;

    parameter real fc = 1M;
    parameter real Q = 0.707;  // Butterworth

    real w0;

    analog begin
        w0 = 2 * `M_PI * fc;
        V(out) <+ laplace_nd(V(in),
                             {w0*w0},
                             {w0*w0, w0/Q, 1});
    end
endmodule
```

---

## 10. Oscillators

### Ring Oscillator Cell

```verilog-a
module ring_osc_cell(in, out, vdd, vss);
    input in, vdd, vss;
    output out;
    electrical in, out, vdd, vss;

    parameter real td = 1n;     // propagation delay
    parameter real tr = 100p;   // rise/fall time
    parameter real vth = 0.5;   // threshold (normalized)

    real vout;

    analog begin
        // Inverter with delay
        if (V(in) > vth * (V(vdd) - V(vss)) + V(vss))
            vout = V(vss);
        else
            vout = V(vdd);

        V(out) <+ absdelay(transition(vout, 0, tr, tr), td);
    end
endmodule
```

### VCO (Voltage Controlled Oscillator)

```verilog-a
module vco(vctrl, out);
    input vctrl;
    output out;
    electrical vctrl, out;

    parameter real f0 = 1G;       // center frequency
    parameter real kvco = 100M;   // VCO gain (Hz/V)
    parameter real vamp = 1.0;    // output amplitude

    real phase;

    analog begin
        phase = idt(2 * `M_PI * (f0 + kvco * V(vctrl)));
        V(out) <+ vamp * sin(phase);
    end
endmodule
```

---

## Quick Reference Table

| Category | Model | Key Parameters |
|----------|-------|----------------|
| Passive | resistor | r |
| Passive | capacitor | c, ic |
| Passive | inductor | l, ic |
| Source | vsource_sin | vdc, vamp, freq, phase |
| Source | isource_dc | idc |
| Controlled | vcvs, vccs | gain, gm |
| Switch | switch_ideal | Ron, Roff, vth, tr |
| Switch | analog_mux | Ron, Roff, Tr |
| Amplifier | opamp_realistic | Adc, gbw, sr, rin |
| Comparator | comparator_hyst | vhyst, tr |
| Converter | dac_ideal | N (bits), tr |
| Filter | lpf_1st, lpf_2nd | fc, Q |
| Oscillator | vco | f0, kvco, vamp |
