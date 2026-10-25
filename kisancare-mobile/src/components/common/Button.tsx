import React from 'react';
import {
  TouchableOpacity,
  Text,
  StyleSheet,
  ActivityIndicator,
  ViewStyle,
  TextStyle,
  StyleProp,
  View,
} from 'react-native';
import { Colors, BorderRadius, Spacing, Typography, Layout } from '@/constants/theme';
import { useColorScheme } from '@/hooks/use-color-scheme';
import { Ionicons } from '@expo/vector-icons';

type IconName = keyof typeof Ionicons.glyphMap;

interface ButtonProps {
  title: string;
  onPress: () => void;
  variant?: 'primary' | 'secondary' | 'outline' | 'accent';
  size?: 'sm' | 'md' | 'lg';
  icon?: IconName;
  iconPosition?: 'left' | 'right';
  loading?: boolean;
  disabled?: boolean;
  style?: StyleProp<ViewStyle>;
  textStyle?: StyleProp<TextStyle>;
}

export const Button: React.FC<ButtonProps> = ({
  title,
  onPress,
  variant = 'primary',
  size = 'md',
  icon,
  iconPosition = 'left',
  loading = false,
  disabled = false,
  style,
  textStyle,
}) => {
  const colorScheme = useColorScheme();
  const theme = Colors[colorScheme ?? 'light'];

  const getContainerStyles = (): ViewStyle => {
    let bg: string = theme.primary;
    let border: string = 'transparent';
    let borderWidth = 0;

    switch (variant) {
      case 'secondary':
        bg = theme.primaryContainer;
        break;
      case 'outline':
        bg = 'transparent';
        border = theme.primary;
        borderWidth = 1.5;
        break;
      case 'accent':
        bg = theme.accent;
        break;
      case 'primary':
      default:
        bg = theme.primary;
        break;
    }

    let height: number = Layout.minTouchTarget;
    let paddingHorizontal: number = Spacing.five;

    if (size === 'sm') {
      height = 40;
      paddingHorizontal = Spacing.three;
    } else if (size === 'lg') {
      height = 56;
      paddingHorizontal = Spacing.six;
    }

    return {
      backgroundColor: disabled ? (colorScheme === 'dark' ? '#2A382C' : '#E0E7E1') : bg,
      borderColor: disabled ? 'transparent' : border,
      borderWidth,
      height,
      paddingHorizontal,
      opacity: disabled ? 0.7 : 1,
    };
  };

  const getTextStyles = (): TextStyle => {
    let color: string = '#FFFFFF';

    switch (variant) {
      case 'secondary':
        color = theme.primary;
        break;
      case 'outline':
        color = theme.primary;
        break;
      case 'accent':
        color = '#FFFFFF';
        break;
      case 'primary':
      default:
        color = '#FFFFFF';
        break;
    }

    if (disabled) {
      color = colorScheme === 'dark' ? '#6B826F' : '#8A9E8D';
    }

    let fontSize: number = Typography.sizes.md;
    if (size === 'sm') fontSize = Typography.sizes.sm;
    if (size === 'lg') fontSize = Typography.sizes.lg;

    return {
      color,
      fontSize,
      fontWeight: Typography.weights.bold,
    };
  };

  const textStyleObj = getTextStyles();
  const iconColor = typeof textStyleObj.color === 'string' ? textStyleObj.color : '#FFFFFF';
  const iconSize = size === 'sm' ? 16 : size === 'lg' ? 22 : 18;

  return (
    <TouchableOpacity
      style={[styles.base, getContainerStyles(), style]}
      onPress={onPress}
      disabled={disabled || loading}
      activeOpacity={0.8}
      accessible={true}
      accessibilityRole="button"
    >
      {loading ? (
        <ActivityIndicator color={iconColor} size="small" />
      ) : (
        <View style={styles.contentRow}>
          {icon && iconPosition === 'left' && (
            <Ionicons name={icon} size={iconSize} color={iconColor} style={styles.leftIcon} />
          )}
          <Text style={[styles.text, textStyleObj, textStyle]}>{title}</Text>
          {icon && iconPosition === 'right' && (
            <Ionicons name={icon} size={iconSize} color={iconColor} style={styles.rightIcon} />
          )}
        </View>
      )}
    </TouchableOpacity>
  );
};

const styles = StyleSheet.create({
  base: {
    borderRadius: BorderRadius.md,
    flexDirection: 'row',
    alignItems: 'center',
    justifyContent: 'center',
  },
  contentRow: {
    flexDirection: 'row',
    alignItems: 'center',
    justifyContent: 'center',
  },
  text: {
    textAlign: 'center',
  },
  leftIcon: {
    marginRight: Spacing.two,
  },
  rightIcon: {
    marginLeft: Spacing.two,
  },
});
