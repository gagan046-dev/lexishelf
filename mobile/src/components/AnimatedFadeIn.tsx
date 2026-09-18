import React from "react";
import Animated, { FadeInDown } from "react-native-reanimated";

type Props = {
  index?: number;
  children: React.ReactNode;
  style?: any;
};

/** Wraps list items so they fade + slide in with a staggered delay based on index. */
export function AnimatedFadeIn({ index = 0, children, style }: Props) {
  return (
    <Animated.View entering={FadeInDown.delay(index * 60).duration(320).springify()} style={style}>
      {children}
    </Animated.View>
  );
}
