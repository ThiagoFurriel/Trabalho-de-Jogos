from dataclasses import dataclass


@dataclass
class CollisionInfo:
    shape_a: object
    shape_b: object
    normal: tuple[float, float]
    overlap: float


class Collide:

    @staticmethod
    def polygon(a, b):

        if not a.bounding_box.colliderect(b.bounding_box):
            return None

        best_collision = None

        for shape_a in a.convex_shapes:
            for shape_b in b.convex_shapes:
                collision = Collide.convex(shape_a.points, shape_b.points)

                if collision is None:
                    continue

                normal, overlap = collision

                if best_collision is None or overlap < best_collision.overlap:
                    best_collision = CollisionInfo(
                        shape_a=shape_a,
                        shape_b=shape_b,
                        normal=normal,
                        overlap=overlap,
                    )

        return best_collision

    @staticmethod
    def convex(a, b):
        smallest_overlap = float("inf")
        smallest_axis = (0, 0)

        for axis in Collide.axes(a) + Collide.axes(b):
            min_a, max_a = Collide.project(a, axis)
            min_b, max_b = Collide.project(b, axis)

            if max_a < min_b or max_b < min_a:
                return None

            overlap = min(max_a, max_b) - max(min_a, min_b)

            if overlap < smallest_overlap:
                smallest_overlap = overlap
                smallest_axis = axis

        center_a = Collide.centroid(a)
        center_b = Collide.centroid(b)

        dx = center_b[0] - center_a[0]
        dy = center_b[1] - center_a[1]

        if dx * smallest_axis[0] + dy * smallest_axis[1] < 0:
            smallest_axis = (-smallest_axis[0], -smallest_axis[1])

        return smallest_axis, smallest_overlap

    @staticmethod
    def axes(points):
        axes = []

        for i in range(len(points)):
            x1, y1 = points[i]
            x2, y2 = points[(i + 1) % len(points)]

            dx = x2 - x1
            dy = y2 - y1

            axis = (-dy, dx)
            length = (axis[0] ** 2 + axis[1] ** 2) ** 0.5

            if length:
                axes.append((
                    axis[0] / length,
                    axis[1] / length,
                ))

        return axes

    @staticmethod
    def centroid(points):
        return (
            sum(p[0] for p in points) / len(points),
            sum(p[1] for p in points) / len(points),
        )

    @staticmethod
    def project(points, axis):
        values = [
            p[0] * axis[0] + p[1] * axis[1]
            for p in points
        ]

        return min(values), max(values)
