# Rebuild the cover plate from the audited transformation. Run at repository root.
png("web/magnitude.png", width = 1100, height = 630, res = 128, bg = "#172f32")
par(mar = c(2.5, 3.8, 0.6, 0.8), fg = "#c8d3b9", col.axis = "#f4eed9",
    family = "sans", xaxs = "i", yaxs = "i", mgp = c(2, 0.65, 0))
t <- seq(-2, 2, length.out = 801)
plot(t, t^2, type = "n", xlim = c(-2.05, 2.05), ylim = c(-0.12, 4.15),
     axes = FALSE, ann = FALSE)
abline(v = seq(-2, 2, 0.125), h = seq(0, 4, 0.125), col = "#244044", lwd = 0.5)
abline(v = -2:2, h = 0:4, col = "#506963", lwd = 0.8)
axis(1, at = -2:2, labels = c(".01", ".1", "1", "10", "100"), tck = -0.013)
axis(2, at = 0:4, labels = c("1", "10", "100", "1,000", "10,000"), las = 1, tck = -0.013)
lines(t, t^2, lwd = 3, col = "#f4ce72")
points(-2:2, (-2:2)^2, pch = 21, cex = 1.35, bg = "#f4ce72", col = "#172f32", lwd = 1.3)
invisible(dev.off())
