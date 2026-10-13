<?php

namespace App\Support;

use Illuminate\Support\Facades\DB;
use Symfony\Component\HttpKernel\Exception\HttpException;

final class ProjectPalette
{
    public static function colors(): array
    {
        $colors = ['#edf7df', '#e3f2fd', '#fff4df', '#dff6f2', '#e3eefb', '#f1f7df', '#e2f4e5', '#e8f6fc'];
        // Limit hues to yellow, green, teal and blue; every shade remains pale.
        foreach ([0.93, 0.95, 0.91] as $lightness) {
            foreach ([0.45, 0.65] as $saturation) {
                for ($hue = 40; $hue <= 210; $hue += 5) {
                    $channel = static function (int $offset) use ($hue, $lightness, $saturation): int {
                        $k = fmod($offset + $hue / 30, 12);
                        $a = $saturation * min($lightness, 1 - $lightness);

                        return (int) round(255 * ($lightness - $a * max(-1, min($k - 3, 9 - $k, 1))));
                    };
                    $colors[] = sprintf('#%02x%02x%02x', $channel(0), $channel(8), $channel(4));
                }
            }
        }

        return array_values(array_unique($colors));
    }

    public static function next(): string
    {
        $used = array_fill_keys(DB::table('projects')->pluck('color')->all(), true);
        foreach (self::colors() as $color) {
            if (! isset($used[$color])) {
                return $color;
            }
        }

        throw new HttpException(503, '利用できるプロジェクト色がありません。既存の色は再利用しません。');
    }
}
