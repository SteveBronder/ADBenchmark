library(data.table)
library(ggplot2)
library(scales)
l
blah = fread("../../../ADBenchmark/docs/data/regression.csv")
blah_flat = melt(blah, id.vars = "N")
ggplot(blah_flat, aes(x = N, y = value / 1e6, color = variable, group = variable)) +
  geom_line() +
  geom_point() +
  scale_y_log10(
    labels = label_number(scale_cut = cut_short_scale(), suffix = " ms")
  ) +
  scale_x_log10(
    labels = label_number(scale_cut = cut_short_scale())
  ) +
  labs(
    x = "N",
    y = "Time (ms)"
  ) +
  theme_bw()

